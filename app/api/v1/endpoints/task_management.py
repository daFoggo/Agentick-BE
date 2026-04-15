from contextlib import nullcontext
from typing import List

from fastapi import APIRouter, Depends

from app.core.dependencies import get_current_active_user, get_db
from app.model.user import User
from app.repository.task_status_repository import TaskStatusRepository
from app.repository.task_type_repository import TaskTypeRepository
from app.repository.task_priority_repository import TaskPriorityRepository
from app.repository.phase_repository import PhaseRepository
from app.repository.tag_repository import TagRepository
from app.schema.base_schema import FindResult, ResponseSchema
from app.schema.task_status_schema import TaskStatusCreate, TaskStatusFind, TaskStatusRead, TaskStatusUpdate
from app.schema.task_type_schema import TaskTypeCreate, TaskTypeFind, TaskTypeRead, TaskTypeUpdate
from app.schema.task_priority_schema import TaskPriorityCreate, TaskPriorityFind, TaskPriorityRead, TaskPriorityUpdate
from app.schema.phase_schema import PhaseCreate, PhaseFind, PhaseRead, PhaseUpdate
from app.schema.tag_schema import TagCreate, TagFind, TagRead, TagUpdate
from app.services.task_status_service import TaskStatusService
from app.services.task_type_service import TaskTypeService
from app.services.task_priority_service import TaskPriorityService
from app.services.phase_service import PhaseService
from app.services.tag_service import TagService

router = APIRouter(tags=["task-management"])

# TaskStatus dependencies and routes
def get_task_status_service(db=Depends(get_db)) -> TaskStatusService:
    task_status_repository = TaskStatusRepository(lambda: nullcontext(db))
    return TaskStatusService(repository=task_status_repository)


@router.post("/statuses", response_model=ResponseSchema[TaskStatusRead])
def create_task_status(
    schema: TaskStatusCreate,
    current_user: User = Depends(get_current_active_user),
    service: TaskStatusService = Depends(get_task_status_service),
):
    result = service.add(schema)
    return ResponseSchema(data=result, message="Task status created successfully")


@router.get("/statuses", response_model=ResponseSchema[FindResult[TaskStatusRead]])
def get_task_statuses(
    find_query: TaskStatusFind = Depends(),
    current_user: User = Depends(get_current_active_user),
    service: TaskStatusService = Depends(get_task_status_service),
):
    result = service.get_list(find_query)
    return ResponseSchema(data=result)


@router.get("/statuses/{status_id}", response_model=ResponseSchema[TaskStatusRead])
def get_task_status(
    status_id: str,
    current_user: User = Depends(get_current_active_user),
    service: TaskStatusService = Depends(get_task_status_service),
):
    result = service.get_by_id(status_id)
    return ResponseSchema(data=result)


@router.patch("/statuses/{status_id}", response_model=ResponseSchema[TaskStatusRead])
def update_task_status(
    status_id: str,
    schema: TaskStatusUpdate,
    current_user: User = Depends(get_current_active_user),
    service: TaskStatusService = Depends(get_task_status_service),
):
    result = service.patch(status_id, schema)
    return ResponseSchema(data=result, message="Task status updated successfully")


@router.delete("/statuses/{status_id}", response_model=ResponseSchema[bool])
def delete_task_status(
    status_id: str,
    current_user: User = Depends(get_current_active_user),
    service: TaskStatusService = Depends(get_task_status_service),
):
    service.remove_by_id(status_id)
    return ResponseSchema(data=True, message="Task status deleted successfully")


# TaskType dependencies and routes
def get_task_type_service(db=Depends(get_db)) -> TaskTypeService:
    task_type_repository = TaskTypeRepository(lambda: nullcontext(db))
    return TaskTypeService(repository=task_type_repository)


@router.post("/types", response_model=ResponseSchema[TaskTypeRead])
def create_task_type(
    schema: TaskTypeCreate,
    current_user: User = Depends(get_current_active_user),
    service: TaskTypeService = Depends(get_task_type_service),
):
    result = service.add(schema)
    return ResponseSchema(data=result, message="Task type created successfully")


@router.get("/types", response_model=ResponseSchema[FindResult[TaskTypeRead]])
def get_task_types(
    find_query: TaskTypeFind = Depends(),
    current_user: User = Depends(get_current_active_user),
    service: TaskTypeService = Depends(get_task_type_service),
):
    result = service.get_list(find_query)
    return ResponseSchema(data=result)


@router.get("/types/{type_id}", response_model=ResponseSchema[TaskTypeRead])
def get_task_type(
    type_id: str,
    current_user: User = Depends(get_current_active_user),
    service: TaskTypeService = Depends(get_task_type_service),
):
    result = service.get_by_id(type_id)
    return ResponseSchema(data=result)


@router.patch("/types/{type_id}", response_model=ResponseSchema[TaskTypeRead])
def update_task_type(
    type_id: str,
    schema: TaskTypeUpdate,
    current_user: User = Depends(get_current_active_user),
    service: TaskTypeService = Depends(get_task_type_service),
):
    result = service.patch(type_id, schema)
    return ResponseSchema(data=result, message="Task type updated successfully")


@router.delete("/types/{type_id}", response_model=ResponseSchema[bool])
def delete_task_type(
    type_id: str,
    current_user: User = Depends(get_current_active_user),
    service: TaskTypeService = Depends(get_task_type_service),
):
    service.remove_by_id(type_id)
    return ResponseSchema(data=True, message="Task type deleted successfully")


# TaskPriority dependencies and routes
def get_task_priority_service(db=Depends(get_db)) -> TaskPriorityService:
    task_priority_repository = TaskPriorityRepository(lambda: nullcontext(db))
    return TaskPriorityService(repository=task_priority_repository)


@router.post("/priorities", response_model=ResponseSchema[TaskPriorityRead])
def create_task_priority(
    schema: TaskPriorityCreate,
    current_user: User = Depends(get_current_active_user),
    service: TaskPriorityService = Depends(get_task_priority_service),
):
    result = service.add(schema)
    return ResponseSchema(data=result, message="Task priority created successfully")


@router.get("/priorities", response_model=ResponseSchema[FindResult[TaskPriorityRead]])
def get_task_priorities(
    find_query: TaskPriorityFind = Depends(),
    current_user: User = Depends(get_current_active_user),
    service: TaskPriorityService = Depends(get_task_priority_service),
):
    result = service.get_list(find_query)
    return ResponseSchema(data=result)


@router.get("/priorities/{priority_id}", response_model=ResponseSchema[TaskPriorityRead])
def get_task_priority(
    priority_id: str,
    current_user: User = Depends(get_current_active_user),
    service: TaskPriorityService = Depends(get_task_priority_service),
):
    result = service.get_by_id(priority_id)
    return ResponseSchema(data=result)


@router.patch("/priorities/{priority_id}", response_model=ResponseSchema[TaskPriorityRead])
def update_task_priority(
    priority_id: str,
    schema: TaskPriorityUpdate,
    current_user: User = Depends(get_current_active_user),
    service: TaskPriorityService = Depends(get_task_priority_service),
):
    result = service.patch(priority_id, schema)
    return ResponseSchema(data=result, message="Task priority updated successfully")


@router.delete("/priorities/{priority_id}", response_model=ResponseSchema[bool])
def delete_task_priority(
    priority_id: str,
    current_user: User = Depends(get_current_active_user),
    service: TaskPriorityService = Depends(get_task_priority_service),
):
    service.remove_by_id(priority_id)
    return ResponseSchema(data=True, message="Task priority deleted successfully")
