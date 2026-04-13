from fastapi import APIRouter

from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.users import router as users_router
from app.api.v1.endpoints.teams import router as teams_router

router = APIRouter(tags=["v1"])
router.include_router(auth_router)
router.include_router(users_router)
router.include_router(teams_router)


@router.get("/ping")
def ping_v1() -> dict[str, str]:
    return {"message": "pong", "version": "v1"}
