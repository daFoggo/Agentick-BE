from datetime import datetime
from contextlib import nullcontext

from fastapi import APIRouter, Depends

from app.core.dependencies import get_current_active_user, get_db
from app.model.user import User
from app.repository.task_repository import TaskRepository
from app.repository.project_member_repository import ProjectMemberRepository
from app.repository.project_repository import ProjectRepository
from app.repository.team_member_repository import TeamMemberRepository
from app.schema.base_schema import FindResult, ResponseSchema
from app.schema.task_schema import TaskCreate, TaskFind, TaskRead, TaskUpdate
from app.schema.task_activity_schema import TaskActivityRead, TaskActivityCreate
from app.services.task_service import TaskService
from app.services.project_permission_service import ProjectPermissionService

router = APIRouter(prefix="/tasks", tags=["tasks"])


def get_task_service(db=Depends(get_db)) -> TaskService:
    task_repository = TaskRepository(lambda: nullcontext(db))
    return TaskService(repository=task_repository)


def get_project_permission_service(db=Depends(get_db)) -> ProjectPermissionService:
    return ProjectPermissionService(
        project_repository=ProjectRepository(lambda: nullcontext(db)),
        project_member_repository=ProjectMemberRepository(lambda: nullcontext(db)),
        team_member_repository=TeamMemberRepository(lambda: nullcontext(db)),
        task_repository=TaskRepository(lambda: nullcontext(db)),
    )


@router.post("", response_model=ResponseSchema[TaskRead])
def create_task(
    schema: TaskCreate,
    current_user: User = Depends(get_current_active_user),
    service: TaskService = Depends(get_task_service),
    permission_service: ProjectPermissionService = Depends(
        get_project_permission_service
    ),
):
    permission_service.ensure_project_task_write(schema.project_id, current_user.id)
    result = service.add(schema, acting_user_id=current_user.id)
    return ResponseSchema(data=result, message="Task created successfully")


@router.get("", response_model=ResponseSchema[FindResult[TaskRead]])
def get_tasks(
    find_query: TaskFind = Depends(),
    current_user: User = Depends(get_current_active_user),
    service: TaskService = Depends(get_task_service),
    permission_service: ProjectPermissionService = Depends(
        get_project_permission_service
    ),
):
    if find_query.project_id__eq:
        permission_service.ensure_project_read(
            find_query.project_id__eq, current_user.id
        )
    elif find_query.member_user_id__eq != current_user.id:
        find_query.member_user_id__eq = current_user.id
    result = service.get_list(find_query)
    return ResponseSchema(data=result)


@router.get("/{task_id}", response_model=ResponseSchema[TaskRead])
def get_task(
    task_id: str,
    current_user: User = Depends(get_current_active_user),
    service: TaskService = Depends(get_task_service),
    permission_service: ProjectPermissionService = Depends(
        get_project_permission_service
    ),
):
    permission_service.ensure_task_read(task_id, current_user.id)
    result = service.get_by_id(task_id)
    return ResponseSchema(data=result)


@router.patch("/{task_id}", response_model=ResponseSchema[TaskRead])
def update_task(
    task_id: str,
    schema: TaskUpdate,
    current_user: User = Depends(get_current_active_user),
    service: TaskService = Depends(get_task_service),
    permission_service: ProjectPermissionService = Depends(
        get_project_permission_service
    ),
):
    permission_service.ensure_task_write(task_id, current_user.id)
    result = service.patch(task_id, schema, user_id=current_user.id)
    return ResponseSchema(data=result, message="Task updated successfully")


@router.delete("/{task_id}", response_model=ResponseSchema[bool])
def delete_task(
    task_id: str,
    current_user: User = Depends(get_current_active_user),
    service: TaskService = Depends(get_task_service),
    permission_service: ProjectPermissionService = Depends(
        get_project_permission_service
    ),
):
    permission_service.ensure_task_write(task_id, current_user.id)
    service.patch_attr(task_id, "is_deleted", True)
    return ResponseSchema(data=True, message="Task deleted successfully")


@router.post("/{task_id}/start", response_model=ResponseSchema[TaskRead])
def start_task(
    task_id: str,
    current_user: User = Depends(get_current_active_user),
    service: TaskService = Depends(get_task_service),
    permission_service: ProjectPermissionService = Depends(
        get_project_permission_service
    ),
):
    permission_service.ensure_task_write(task_id, current_user.id)
    result = service.start_task(task_id, user_id=current_user.id)
    return ResponseSchema(data=result, message="Task marked as started")


@router.post("/{task_id}/complete", response_model=ResponseSchema[TaskRead])
def complete_task(
    task_id: str,
    completed_at: datetime | None = None,
    current_user: User = Depends(get_current_active_user),
    service: TaskService = Depends(get_task_service),
    permission_service: ProjectPermissionService = Depends(
        get_project_permission_service
    ),
):
    permission_service.ensure_task_write(task_id, current_user.id)
    result = service.complete_task(
        task_id, user_id=current_user.id, completed_at=completed_at
    )
    return ResponseSchema(data=result, message="Task successfully finalized")


@router.get(
    "/{task_id}/activities", response_model=ResponseSchema[list[TaskActivityRead]]
)
def get_task_activities(
    task_id: str,
    current_user: User = Depends(get_current_active_user),
    service: TaskService = Depends(get_task_service),
    permission_service: ProjectPermissionService = Depends(
        get_project_permission_service
    ),
):
    permission_service.ensure_task_read(task_id, current_user.id)
    result = service.get_task_activities(task_id)
    return ResponseSchema(data=result)


@router.post("/{task_id}/comments", response_model=ResponseSchema[TaskActivityRead])
def create_task_comment(
    task_id: str,
    payload: TaskActivityCreate,
    current_user: User = Depends(get_current_active_user),
    service: TaskService = Depends(get_task_service),
    permission_service: ProjectPermissionService = Depends(
        get_project_permission_service
    ),
):
    permission_service.ensure_task_write(task_id, current_user.id)
    # We use payload.content directly. Note that we ignore payload.task_id passed in json in favor of URL param
    result = service.create_comment(
        task_id=task_id, user_id=current_user.id, content=payload.content
    )
    return ResponseSchema(data=result)
