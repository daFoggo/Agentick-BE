from contextlib import nullcontext

from fastapi import APIRouter, Depends

from app.core.dependencies import get_current_active_user, get_db
from app.core.exceptions import NotFoundError
from app.model.user import User
from app.repository.task_repository import TaskRepository
from app.schema.base_schema import FindResult, ResponseSchema
from app.schema.task_schema import TaskCreate, TaskFind, TaskRead, TaskUpdate
from app.services.task_service import TaskService

router = APIRouter(prefix="/projects/{project_id}/tasks", tags=["project-tasks"])


def get_task_service(db=Depends(get_db)) -> TaskService:
    task_repository = TaskRepository(lambda: nullcontext(db))
    return TaskService(repository=task_repository)


def _ensure_task_in_project(task: TaskRead, project_id: str):
    if task.project_id != project_id:
        raise NotFoundError(detail="Task not found.")


@router.post("", response_model=ResponseSchema[TaskRead])
def create_project_task(
    project_id: str,
    schema: TaskCreate,
    current_user: User = Depends(get_current_active_user),
    service: TaskService = Depends(get_task_service),
):
    scoped_schema = schema.model_copy(update={"project_id": project_id})
    result = service.add(scoped_schema)
    return ResponseSchema(data=result, message="Task created successfully")


@router.get("", response_model=ResponseSchema[FindResult[TaskRead]])
def get_project_tasks(
    project_id: str,
    find_query: TaskFind = Depends(),
    current_user: User = Depends(get_current_active_user),
    service: TaskService = Depends(get_task_service),
):
    scoped_find = find_query.model_copy(update={"project_id__eq": project_id})
    result = service.get_list(scoped_find)
    return ResponseSchema(data=result)


@router.get("/{task_id}", response_model=ResponseSchema[TaskRead])
def get_project_task(
    project_id: str,
    task_id: str,
    current_user: User = Depends(get_current_active_user),
    service: TaskService = Depends(get_task_service),
):
    result = service.get_by_id(task_id)
    _ensure_task_in_project(result, project_id)
    return ResponseSchema(data=result)


@router.patch("/{task_id}", response_model=ResponseSchema[TaskRead])
def update_project_task(
    project_id: str,
    task_id: str,
    schema: TaskUpdate,
    current_user: User = Depends(get_current_active_user),
    service: TaskService = Depends(get_task_service),
):
    task = service.get_by_id(task_id)
    _ensure_task_in_project(task, project_id)
    result = service.patch(task_id, schema)
    return ResponseSchema(data=result, message="Task updated successfully")


@router.delete("/{task_id}", response_model=ResponseSchema[bool])
def delete_project_task(
    project_id: str,
    task_id: str,
    current_user: User = Depends(get_current_active_user),
    service: TaskService = Depends(get_task_service),
):
    task = service.get_by_id(task_id)
    _ensure_task_in_project(task, project_id)
    service.patch_attr(task_id, "is_deleted", True)
    return ResponseSchema(data=True, message="Task deleted successfully")
