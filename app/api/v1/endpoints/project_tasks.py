from contextlib import nullcontext
from datetime import datetime, timedelta, timezone
from typing import Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func

from app.core.dependencies import get_current_active_user, get_db
from app.core.exceptions import NotFoundError
from app.model.user import User
from app.model.task import Task
from app.model.task_status import TaskStatus
from app.model.task_type import TaskType
from app.model.task_priority import TaskPriority
from app.repository.task_repository import TaskRepository
from app.schema.base_schema import FindResult, ResponseSchema
from app.schema.task_schema import (
    TaskCreate, TaskFind, TaskRead, TaskUpdate,
    ProjectTaskStats, TaskStatItem,
)
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


# NOTE: /stats phải đứng TRƯỜC /{task_id} để FastAPI không match sai route
@router.get("/stats", response_model=ResponseSchema[ProjectTaskStats])
def get_project_task_stats(
    project_id: str,
    period: Literal["weekly", "monthly"] = Query(default="weekly"),
    current_user: User = Depends(get_current_active_user),
    db=Depends(get_db),
):
    """
    Thống kê task của project theo Priority, Status và Type.
    Dùng cho biểu đồ ProjectTaskStatsCard trên Dashboard.
    - weekly: tuần hiện tại (Thứ Hai → Chủ Nhật)
    - monthly: 30 ngày gần nhất
    """
    now = datetime.now(timezone.utc)

    # weekly = 7 ngày qua, monthly = 30 ngày qua
    delta = timedelta(days=7) if period == "weekly" else timedelta(days=30)
    date_from = now - delta
    date_to = now

    shared_filters = [
        Task.project_id == project_id,
        Task.is_deleted.is_(False),
        Task.is_archived.is_(False),
        Task.updated_at >= date_from,
        Task.updated_at < date_to,   # upper bound: loại task được update sau "bây giờ"
    ]

    # ── By Priority ─────────────────────────────────────────────────────────────────────────
    priority_rows = (
        db.query(TaskPriority.id, TaskPriority.name, TaskPriority.color, func.count(Task.id))
        .join(Task, Task.priority_id == TaskPriority.id)
        .filter(*shared_filters)
        .group_by(TaskPriority.id, TaskPriority.name, TaskPriority.color)
        .all()
    )
    by_priority = [TaskStatItem(id=r[0], name=r[1], color=r[2], count=r[3]) for r in priority_rows]

    # ── By Status ──────────────────────────────────────────────────────────────────────────
    status_rows = (
        db.query(TaskStatus.id, TaskStatus.name, TaskStatus.color, func.count(Task.id))
        .join(Task, Task.status_id == TaskStatus.id)
        .filter(*shared_filters)
        .group_by(TaskStatus.id, TaskStatus.name, TaskStatus.color)
        .all()
    )
    by_status = [TaskStatItem(id=r[0], name=r[1], color=r[2], count=r[3]) for r in status_rows]

    # ── By Type ───────────────────────────────────────────────────────────────────────────
    type_rows = (
        db.query(TaskType.id, TaskType.name, TaskType.color, func.count(Task.id))
        .join(Task, Task.type_id == TaskType.id)
        .filter(*shared_filters)
        .group_by(TaskType.id, TaskType.name, TaskType.color)
        .all()
    )
    by_type = [TaskStatItem(id=r[0], name=r[1], color=r[2], count=r[3]) for r in type_rows]

    return ResponseSchema(
        data=ProjectTaskStats(
            by_priority=by_priority,
            by_status=by_status,
            by_type=by_type,
            period=period,
            date_from=date_from.date().isoformat(),
            date_to=date_to.date().isoformat(),
        ),
        message="Task stats fetched successfully",
    )


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




