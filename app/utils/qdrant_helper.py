import os
import hashlib
import httpx
import asyncio


def run_async_background(coro):
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(coro)
    except RuntimeError:
        asyncio.run(coro)


QDRANT_HOST = os.getenv("QDRANT_HOST", "qdrant")
QDRANT_URL = f"http://{QDRANT_HOST}:6333"
COLLECTION_NAME = "tasks"


def get_pseudo_embedding(text: str) -> list[float]:
    # Generates a deterministic 768-dimensional float list from the text hash
    embedding = []
    text_bytes = text.encode("utf-8")
    for i in range(768):
        h = hashlib.sha256(text_bytes + str(i).encode("utf-8")).hexdigest()
        val = int(h[:8], 16) / 4294967295.0  # normalized between 0.0 and 1.0
        embedding.append(val)
    return embedding


async def get_google_embedding(text: str) -> list[float]:
    api_key = (
        os.getenv("GEMINI_API_KEY")
        or os.getenv("GOOGLE_API_KEY")
        or os.getenv("OPENROUTER_API_KEY")
    )
    if not api_key:
        return get_pseudo_embedding(text)

    try:
        async with httpx.AsyncClient() as client:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/text-embedding-004:embedContent?key={api_key}"
            res = await client.post(
                url, json={"content": {"parts": [{"text": text}]}}, timeout=10.0
            )
            if res.status_code == 200:
                data = res.json()
                return data["embedding"]["values"]
    except Exception:
        pass

    return get_pseudo_embedding(text)


async def init_qdrant():
    global QDRANT_URL
    async with httpx.AsyncClient() as client:
        for host in ["qdrant", "localhost"]:
            url = f"http://{host}:6333"
            try:
                res = await client.get(f"{url}/collections", timeout=2.0)
                if res.status_code == 200:
                    QDRANT_URL = url
                    break
            except Exception:
                continue

        # Create collection if it doesn't exist
        try:
            res = await client.get(f"{QDRANT_URL}/v1/collections/{COLLECTION_NAME}")
            if res.status_code != 200:
                payload = {"vectors": {"size": 768, "distance": "Cosine"}}
                await client.put(
                    f"{QDRANT_URL}/v1/collections/{COLLECTION_NAME}",
                    json=payload,
                    timeout=5.0,
                )
        except Exception as e:
            print(f"Failed to initialize Qdrant: {e}")


async def upsert_task_vector(
    task_id: str, title: str, description: str, project_id: str
):
    await init_qdrant()
    text = f"{title} {description or ''}"
    vector = await get_google_embedding(text)

    payload = {
        "points": [
            {
                "id": task_id,
                "vector": vector,
                "payload": {
                    "task_id": task_id,
                    "project_id": project_id,
                    "title": title,
                    "description": description or "",
                },
            }
        ]
    }
    try:
        async with httpx.AsyncClient() as client:
            await client.put(
                f"{QDRANT_URL}/v1/collections/{COLLECTION_NAME}/points",
                json=payload,
                timeout=5.0,
            )
    except Exception as e:
        print(f"Failed to upsert to Qdrant: {e}")


async def search_similar_tasks(project_id: str, query_text: str, limit: int = 5):
    await init_qdrant()
    vector = await get_google_embedding(query_text)

    payload = {
        "vector": vector,
        "filter": {"must": [{"key": "project_id", "match": {"value": project_id}}]},
        "limit": limit,
        "with_payload": True,
    }

    try:
        async with httpx.AsyncClient() as client:
            res = await client.post(
                f"{QDRANT_URL}/v1/collections/{COLLECTION_NAME}/points/search",
                json=payload,
                timeout=5.0,
            )
            if res.status_code == 200:
                data = res.json()
                results = []
                for point in data.get("result", []):
                    results.append(point["payload"])
                return results
    except Exception as e:
        print(f"Qdrant search failed: {e}")
    return []
