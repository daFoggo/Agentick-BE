from contextlib import nullcontext

from fastapi import APIRouter, Depends

from app.core.dependencies import get_current_active_user, get_db
from app.model.user import User
from app.repository.task_repository import TaskRepository
from app.schema.agent_schema import AgentChatRequest, AgentChatResponse
from app.schema.base_schema import ResponseSchema
from app.services.agent_service import AgentService
from app.services.task_service import TaskService

router = APIRouter(prefix="/agent", tags=["agent"])


def get_agent_service(db=Depends(get_db)) -> AgentService:
    task_repository = TaskRepository(lambda: nullcontext(db))
    task_service = TaskService(repository=task_repository)
    return AgentService(task_service=task_service)


@router.post("/chat", response_model=ResponseSchema[AgentChatResponse])
async def chat_with_agent(
    payload: AgentChatRequest,
    current_user: User = Depends(get_current_active_user),
    service: AgentService = Depends(get_agent_service),
):
    result = await service.run_agent(
        project_id=payload.project_id, prompt=payload.message, history=payload.history
    )
    return ResponseSchema(data=result, message="Agent processed request successfully")
