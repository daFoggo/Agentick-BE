from fastapi import APIRouter

router = APIRouter(tags=["v2"])


@router.get("/ping")
def ping_v2() -> dict[str, str]:
    return {"message": "pong", "version": "v2"}
