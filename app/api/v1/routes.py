from fastapi import APIRouter

router = APIRouter(tags=["v1"])


@router.get("/ping")
def ping_v1() -> dict[str, str]:
    return {"message": "pong", "version": "v1"}
