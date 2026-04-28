from fastapi import APIRouter

from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.users import router as users_router
from app.api.v1.endpoints.teams import router as teams_router
from app.api.v1.endpoints.projects import router as projects_router
from app.api.v1.endpoints.project_tasks import router as project_tasks_router
from app.api.v1.endpoints.project_task_config import router as project_task_config_router
from app.api.v1.endpoints.project_phases import router as project_phases_router
from app.api.v1.endpoints.invitations import router as invitations_router

router = APIRouter(tags=["v1"])
router.include_router(auth_router)
router.include_router(users_router)
router.include_router(teams_router)
router.include_router(projects_router)
router.include_router(project_tasks_router)
router.include_router(project_task_config_router)
router.include_router(project_phases_router)
router.include_router(invitations_router)


@router.get("/ping")
def ping_v1() -> dict[str, str]:
    return {"message": "pong", "version": "v1"}
