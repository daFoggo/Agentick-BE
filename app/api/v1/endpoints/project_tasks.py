from contextlib import nullcontext
from typing import Literal

from fastapi import APIRouter, Depends, Query

from app.core.dependencies import get_current_active_user, get_db
from app.core.exceptions import NotFoundError
from app.model.user import User
from app.repository.task_repository import TaskRepository
from app.repository.project_member_repository import ProjectMemberRepository
from app.repository.project_repository import ProjectRepository
from app.repository.team_member_repository import TeamMemberRepository
from app.schema.base_schema import FindResult, ResponseSchema
from app.schema.task_schema import (
    ProjectTaskStats,
    TaskCreate,
    TaskFind,
    TaskRead,
    TaskUpdate,
)
from app.services.task_service import TaskService
from app.services.project_permission_service import ProjectPermissionService

router = APIRouter(prefix="/projects/{project_id}/tasks", tags=["project-tasks"])


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


def _ensure_task_in_project(task: TaskRead, project_id: str):
    if task.project_id != project_id:
        raise NotFoundError(detail="Task not found.")


@router.post("", response_model=ResponseSchema[TaskRead])
def create_project_task(
    project_id: str,
    schema: TaskCreate,
    current_user: User = Depends(get_current_active_user),
    service: TaskService = Depends(get_task_service),
    permission_service: ProjectPermissionService = Depends(
        get_project_permission_service
    ),
):
    permission_service.ensure_project_task_write(project_id, current_user.id)
    scoped_schema = schema.model_copy(update={"project_id": project_id})
    result = service.add(scoped_schema, acting_user_id=current_user.id)
    return ResponseSchema(data=result, message="Task created successfully")


@router.get("", response_model=ResponseSchema[FindResult[TaskRead]])
def get_project_tasks(
    project_id: str,
    find_query: TaskFind = Depends(),
    current_user: User = Depends(get_current_active_user),
    service: TaskService = Depends(get_task_service),
    permission_service: ProjectPermissionService = Depends(
        get_project_permission_service
    ),
):
    permission_service.ensure_project_read(project_id, current_user.id)
    scoped_find = find_query.model_copy(update={"project_id__eq": project_id})
    result = service.get_list(scoped_find)
    return ResponseSchema(data=result)


# NOTE: /stats phải đứng TRƯỜC /{task_id} để FastAPI không match sai route
@router.get("/stats", response_model=ResponseSchema[ProjectTaskStats])
def get_project_task_stats(
    project_id: str,
    period: Literal["weekly", "monthly"] = Query(default="weekly"),
    current_user: User = Depends(get_current_active_user),
    service: TaskService = Depends(get_task_service),
    permission_service: ProjectPermissionService = Depends(
        get_project_permission_service
    ),
):
    """
    Thống kê task của project theo Priority, Status và Type.
    Dùng cho biểu đồ ProjectTaskStatsCard trên Dashboard.
    - weekly: tuần hiện tại (Thứ Hai → Chủ Nhật)
    - monthly: 30 ngày gần nhất
    """
    permission_service.ensure_project_read(project_id, current_user.id)
    result = service.get_project_stats(project_id, period)
    return ResponseSchema(data=result, message="Task stats fetched successfully")


@router.get("/risk-stats", response_model=ResponseSchema[dict])
def get_project_risk_stats(
    project_id: str,
    current_user: User = Depends(get_current_active_user),
    service: TaskService = Depends(get_task_service),
    permission_service: ProjectPermissionService = Depends(
        get_project_permission_service
    ),
):
    """
    Get aggregated risk statistics for the dashboard.
    Calculates overall project risk index, task risk distribution, and risk matrix points.
    """
    permission_service.ensure_project_read(project_id, current_user.id)
    result = service.get_risk_stats(project_id)
    return ResponseSchema(
        data=result,
        message="Risk stats fetched successfully",
    )


@router.get("/recent-updates", response_model=ResponseSchema[list[dict]])
def get_recent_status_updates(
    project_id: str,
    limit: int = Query(default=10, ge=1, le=50),
    current_user: User = Depends(get_current_active_user),
    service: TaskService = Depends(get_task_service),
    permission_service: ProjectPermissionService = Depends(
        get_project_permission_service
    ),
):
    """
    Lấy danh sách các cập nhật trạng thái gần đây của dự án.
    Trộn với bảng Task, User, TaskStatus để trả về dữ liệu hiển thị.
    """
    permission_service.ensure_project_read(project_id, current_user.id)
    results = service.get_recent_updates(project_id, limit)
    return ResponseSchema(data=results, message="Recent updates fetched successfully")


@router.get("/{task_id}", response_model=ResponseSchema[TaskRead])
def get_project_task(
    project_id: str,
    task_id: str,
    current_user: User = Depends(get_current_active_user),
    service: TaskService = Depends(get_task_service),
    permission_service: ProjectPermissionService = Depends(
        get_project_permission_service
    ),
):
    permission_service.ensure_project_read(project_id, current_user.id)
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
    permission_service: ProjectPermissionService = Depends(
        get_project_permission_service
    ),
):
    permission_service.ensure_project_task_write(project_id, current_user.id)
    task = service.get_by_id(task_id)
    _ensure_task_in_project(task, project_id)
    result = service.patch(task_id, schema, user_id=current_user.id)
    return ResponseSchema(data=result, message="Task updated successfully")


@router.delete("/{task_id}", response_model=ResponseSchema[bool])
def delete_project_task(
    project_id: str,
    task_id: str,
    current_user: User = Depends(get_current_active_user),
    service: TaskService = Depends(get_task_service),
    permission_service: ProjectPermissionService = Depends(
        get_project_permission_service
    ),
):
    permission_service.ensure_project_task_write(project_id, current_user.id)
    task = service.get_by_id(task_id)
    _ensure_task_in_project(task, project_id)
    service.patch_attr(task_id, "is_deleted", True)
    return ResponseSchema(data=True, message="Task deleted successfully")
