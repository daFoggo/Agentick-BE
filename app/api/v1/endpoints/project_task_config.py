from contextlib import nullcontext

from fastapi import APIRouter, Depends

from app.core.dependencies import get_current_active_user, get_db
from app.core.exceptions import NotFoundError
from app.model.user import User
from app.repository.tag_repository import TagRepository
from app.repository.task_priority_repository import TaskPriorityRepository
from app.repository.task_status_repository import TaskStatusRepository
from app.repository.task_type_repository import TaskTypeRepository
from app.schema.base_schema import FindResult, ResponseSchema
from app.schema.tag_schema import TagCreate, TagFind, TagRead, TagUpdate
from app.schema.task_priority_schema import TaskPriorityCreate, TaskPriorityFind, TaskPriorityRead, TaskPriorityUpdate
from app.schema.task_status_schema import TaskStatusCreate, TaskStatusFind, TaskStatusRead, TaskStatusUpdate
from app.schema.task_type_schema import TaskTypeCreate, TaskTypeFind, TaskTypeRead, TaskTypeUpdate
from app.services.tag_service import TagService
from app.services.task_priority_service import TaskPriorityService
from app.services.task_status_service import TaskStatusService
from app.services.task_type_service import TaskTypeService

router = APIRouter(prefix="/projects/{project_id}/task-config", tags=["project-task-config"])


def get_task_status_service(db=Depends(get_db)) -> TaskStatusService:
    return TaskStatusService(repository=TaskStatusRepository(lambda: nullcontext(db)))


def get_task_type_service(db=Depends(get_db)) -> TaskTypeService:
    return TaskTypeService(repository=TaskTypeRepository(lambda: nullcontext(db)))


def get_task_priority_service(db=Depends(get_db)) -> TaskPriorityService:
    return TaskPriorityService(repository=TaskPriorityRepository(lambda: nullcontext(db)))


def get_tag_service(db=Depends(get_db)) -> TagService:
    return TagService(repository=TagRepository(lambda: nullcontext(db)))


def _ensure_same_project(record_project_id: str, project_id: str, entity_name: str):
    if record_project_id != project_id:
        raise NotFoundError(detail=f"{entity_name} not found.")


@router.post("/statuses", response_model=ResponseSchema[TaskStatusRead])
def create_status(
    project_id: str,
    schema: TaskStatusCreate,
    current_user: User = Depends(get_current_active_user),
    service: TaskStatusService = Depends(get_task_status_service),
):
    scoped_schema = schema.model_copy(update={"project_id": project_id})
    result = service.add(scoped_schema)
    return ResponseSchema(data=result, message="Task status created successfully")


@router.get("/statuses", response_model=ResponseSchema[FindResult[TaskStatusRead]])
def get_statuses(
    project_id: str,
    find_query: TaskStatusFind = Depends(),
    current_user: User = Depends(get_current_active_user),
    service: TaskStatusService = Depends(get_task_status_service),
):
    scoped_find = find_query.model_copy(update={"project_id__eq": project_id})
    result = service.get_list(scoped_find)
    return ResponseSchema(data=result)


@router.patch("/statuses/{status_id}", response_model=ResponseSchema[TaskStatusRead])
def update_status(
    project_id: str,
    status_id: str,
    schema: TaskStatusUpdate,
    current_user: User = Depends(get_current_active_user),
    service: TaskStatusService = Depends(get_task_status_service),
):
    status = service.get_by_id(status_id)
    _ensure_same_project(status.project_id, project_id, "Task status")
    result = service.patch(status_id, schema)
    return ResponseSchema(data=result, message="Task status updated successfully")


@router.delete("/statuses/{status_id}", response_model=ResponseSchema[bool])
def delete_status(
    project_id: str,
    status_id: str,
    current_user: User = Depends(get_current_active_user),
    service: TaskStatusService = Depends(get_task_status_service),
):
    status = service.get_by_id(status_id)
    _ensure_same_project(status.project_id, project_id, "Task status")
    service.remove_by_id(status_id)
    return ResponseSchema(data=True, message="Task status deleted successfully")


@router.post("/types", response_model=ResponseSchema[TaskTypeRead])
def create_type(
    project_id: str,
    schema: TaskTypeCreate,
    current_user: User = Depends(get_current_active_user),
    service: TaskTypeService = Depends(get_task_type_service),
):
    scoped_schema = schema.model_copy(update={"project_id": project_id})
    result = service.add(scoped_schema)
    return ResponseSchema(data=result, message="Task type created successfully")


@router.get("/types", response_model=ResponseSchema[FindResult[TaskTypeRead]])
def get_types(
    project_id: str,
    find_query: TaskTypeFind = Depends(),
    current_user: User = Depends(get_current_active_user),
    service: TaskTypeService = Depends(get_task_type_service),
):
    scoped_find = find_query.model_copy(update={"project_id__eq": project_id})
    result = service.get_list(scoped_find)
    return ResponseSchema(data=result)


@router.patch("/types/{type_id}", response_model=ResponseSchema[TaskTypeRead])
def update_type(
    project_id: str,
    type_id: str,
    schema: TaskTypeUpdate,
    current_user: User = Depends(get_current_active_user),
    service: TaskTypeService = Depends(get_task_type_service),
):
    task_type = service.get_by_id(type_id)
    _ensure_same_project(task_type.project_id, project_id, "Task type")
    result = service.patch(type_id, schema)
    return ResponseSchema(data=result, message="Task type updated successfully")


@router.delete("/types/{type_id}", response_model=ResponseSchema[bool])
def delete_type(
    project_id: str,
    type_id: str,
    current_user: User = Depends(get_current_active_user),
    service: TaskTypeService = Depends(get_task_type_service),
):
    task_type = service.get_by_id(type_id)
    _ensure_same_project(task_type.project_id, project_id, "Task type")
    service.remove_by_id(type_id)
    return ResponseSchema(data=True, message="Task type deleted successfully")


@router.post("/priorities", response_model=ResponseSchema[TaskPriorityRead])
def create_priority(
    project_id: str,
    schema: TaskPriorityCreate,
    current_user: User = Depends(get_current_active_user),
    service: TaskPriorityService = Depends(get_task_priority_service),
):
    scoped_schema = schema.model_copy(update={"project_id": project_id})
    result = service.add(scoped_schema)
    return ResponseSchema(data=result, message="Task priority created successfully")


@router.get("/priorities", response_model=ResponseSchema[FindResult[TaskPriorityRead]])
def get_priorities(
    project_id: str,
    find_query: TaskPriorityFind = Depends(),
    current_user: User = Depends(get_current_active_user),
    service: TaskPriorityService = Depends(get_task_priority_service),
):
    scoped_find = find_query.model_copy(update={"project_id__eq": project_id})
    result = service.get_list(scoped_find)
    return ResponseSchema(data=result)


@router.patch("/priorities/{priority_id}", response_model=ResponseSchema[TaskPriorityRead])
def update_priority(
    project_id: str,
    priority_id: str,
    schema: TaskPriorityUpdate,
    current_user: User = Depends(get_current_active_user),
    service: TaskPriorityService = Depends(get_task_priority_service),
):
    priority = service.get_by_id(priority_id)
    _ensure_same_project(priority.project_id, project_id, "Task priority")
    result = service.patch(priority_id, schema)
    return ResponseSchema(data=result, message="Task priority updated successfully")


@router.delete("/priorities/{priority_id}", response_model=ResponseSchema[bool])
def delete_priority(
    project_id: str,
    priority_id: str,
    current_user: User = Depends(get_current_active_user),
    service: TaskPriorityService = Depends(get_task_priority_service),
):
    priority = service.get_by_id(priority_id)
    _ensure_same_project(priority.project_id, project_id, "Task priority")
    service.remove_by_id(priority_id)
    return ResponseSchema(data=True, message="Task priority deleted successfully")


@router.post("/tags", response_model=ResponseSchema[TagRead])
def create_tag(
    project_id: str,
    schema: TagCreate,
    current_user: User = Depends(get_current_active_user),
    service: TagService = Depends(get_tag_service),
):
    scoped_schema = schema.model_copy(update={"project_id": project_id})
    result = service.add(scoped_schema)
    return ResponseSchema(data=result, message="Tag created successfully")


@router.get("/tags", response_model=ResponseSchema[FindResult[TagRead]])
def get_tags(
    project_id: str,
    find_query: TagFind = Depends(),
    current_user: User = Depends(get_current_active_user),
    service: TagService = Depends(get_tag_service),
):
    scoped_find = find_query.model_copy(update={"project_id__eq": project_id})
    result = service.get_list(scoped_find)
    return ResponseSchema(data=result)


@router.patch("/tags/{tag_id}", response_model=ResponseSchema[TagRead])
def update_tag(
    project_id: str,
    tag_id: str,
    schema: TagUpdate,
    current_user: User = Depends(get_current_active_user),
    service: TagService = Depends(get_tag_service),
):
    tag = service.get_by_id(tag_id)
    _ensure_same_project(tag.project_id, project_id, "Tag")
    result = service.patch(tag_id, schema)
    return ResponseSchema(data=result, message="Tag updated successfully")


@router.delete("/tags/{tag_id}", response_model=ResponseSchema[bool])
def delete_tag(
    project_id: str,
    tag_id: str,
    current_user: User = Depends(get_current_active_user),
    service: TagService = Depends(get_tag_service),
):
    tag = service.get_by_id(tag_id)
    _ensure_same_project(tag.project_id, project_id, "Tag")
    service.remove_by_id(tag_id)
    return ResponseSchema(data=True, message="Tag deleted successfully")
