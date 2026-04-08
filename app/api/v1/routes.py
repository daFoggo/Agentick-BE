from fastapi import APIRouter

from app.api.v1.endpoints.auth import router as auth_router

router = APIRouter(tags=["v1"])
router.include_router(auth_router)


@router.get("/ping")
def ping_v1() -> dict[str, str]:
    return {"message": "pong", "version": "v1"}
