from contextlib import nullcontext
from typing import List

from fastapi import APIRouter, Depends

from app.core.dependencies import get_current_active_user, get_db
from app.model.user import User
from app.repository.task_repository import TaskRepository
from app.repository.project_repository import ProjectRepository
from app.schema.base_schema import FindResult, ResponseSchema
from app.schema.task_schema import TaskCreate, TaskFind, TaskRead, TaskUpdate
from app.services.task_service import TaskService

router = APIRouter(prefix="/tasks", tags=["tasks"])


def get_task_service(db=Depends(get_db)) -> TaskService:
    task_repository = TaskRepository(lambda: nullcontext(db))
    return TaskService(repository=task_repository)


@router.post("", response_model=ResponseSchema[TaskRead])
def create_task(
    schema: TaskCreate,
    current_user: User = Depends(get_current_active_user),
    service: TaskService = Depends(get_task_service),
):
    result = service.add(schema)
    return ResponseSchema(data=result, message="Task created successfully")


@router.get("", response_model=ResponseSchema[FindResult[TaskRead]])
def get_tasks(
    find_query: TaskFind = Depends(),
    current_user: User = Depends(get_current_active_user),
    service: TaskService = Depends(get_task_service),
):
    result = service.get_list(find_query)
    return ResponseSchema(data=result)


@router.get("/{task_id}", response_model=ResponseSchema[TaskRead])
def get_task(
    task_id: str,
    current_user: User = Depends(get_current_active_user),
    service: TaskService = Depends(get_task_service),
):
    result = service.get_by_id(task_id)
    return ResponseSchema(data=result)


@router.patch("/{task_id}", response_model=ResponseSchema[TaskRead])
def update_task(
    task_id: str,
    schema: TaskUpdate,
    current_user: User = Depends(get_current_active_user),
    service: TaskService = Depends(get_task_service),
):
    result = service.patch(task_id, schema)
    return ResponseSchema(data=result, message="Task updated successfully")


@router.delete("/{task_id}", response_model=ResponseSchema[bool])
def delete_task(
    task_id: str,
    current_user: User = Depends(get_current_active_user),
    service: TaskService = Depends(get_task_service),
):
    service.patch_attr(task_id, "is_deleted", True)
    return ResponseSchema(data=True, message="Task deleted successfully")
