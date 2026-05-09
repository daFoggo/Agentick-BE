from contextlib import nullcontext
from datetime import datetime, timedelta, timezone
from typing import Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import joinedload

from app.core.dependencies import get_current_active_user, get_db
from app.core.exceptions import NotFoundError
from app.model.user import User
from app.model.task_activity import TaskActivity
from app.model.task import Task
from app.model.task_status import TaskStatus
from app.model.task_type import TaskType
from app.model.task_priority import TaskPriority
from app.repository.task_repository import TaskRepository
from app.schema.base_schema import FindResult, ResponseSchema
from app.schema.task_schema import (
    TaskCreate,
    TaskFind,
    TaskRead,
    TaskUpdate,
    ProjectTaskStats,
    TaskStatItem,
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
        Task.updated_at < date_to,  # upper bound: loại task được update sau "bây giờ"
    ]

    # ── By Priority ─────────────────────────────────────────────────────────────────────────
    priority_rows = (
        db.query(
            TaskPriority.id, TaskPriority.name, TaskPriority.color, func.count(Task.id)
        )
        .join(Task, Task.priority_id == TaskPriority.id)
        .filter(*shared_filters)
        .group_by(TaskPriority.id, TaskPriority.name, TaskPriority.color)
        .all()
    )
    by_priority = [
        TaskStatItem(id=r[0], name=r[1], color=r[2], count=r[3]) for r in priority_rows
    ]

    # ── By Status ──────────────────────────────────────────────────────────────────────────
    status_rows = (
        db.query(TaskStatus.id, TaskStatus.name, TaskStatus.color, func.count(Task.id))
        .join(Task, Task.status_id == TaskStatus.id)
        .filter(*shared_filters)
        .group_by(TaskStatus.id, TaskStatus.name, TaskStatus.color)
        .all()
    )
    by_status = [
        TaskStatItem(id=r[0], name=r[1], color=r[2], count=r[3]) for r in status_rows
    ]

    # ── By Type ───────────────────────────────────────────────────────────────────────────
    type_rows = (
        db.query(TaskType.id, TaskType.name, TaskType.color, func.count(Task.id))
        .join(Task, Task.type_id == TaskType.id)
        .filter(*shared_filters)
        .group_by(TaskType.id, TaskType.name, TaskType.color)
        .all()
    )
    by_type = [
        TaskStatItem(id=r[0], name=r[1], color=r[2], count=r[3]) for r in type_rows
    ]

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


@router.get("/risk-stats", response_model=ResponseSchema[dict])
def get_project_risk_stats(
    project_id: str,
    current_user: User = Depends(get_current_active_user),
    db=Depends(get_db),
):
    """
    Get aggregated risk statistics for the dashboard.
    Calculates overall project risk index, task risk distribution, and risk matrix points.
    """
    from app.model.risk_snapshot import RiskSnapshot

    # Lấy các task đang active trong project
    active_tasks = (
        db.query(Task)
        .filter(
            Task.project_id == project_id,
            Task.is_deleted.is_(False),
            Task.is_archived.is_(False),
        )
        .all()
    )

    if not active_tasks:
        return ResponseSchema(data={"overall_risk_index": 0, "tasks": []})

    task_map = {t.id: t for t in active_tasks}
    task_ids = list(task_map.keys())

    # Lấy các risk snapshot mới nhất cho từng task
    snapshots = (
        db.query(RiskSnapshot)
        .filter(RiskSnapshot.task_id.in_(task_ids))
        .order_by(RiskSnapshot.created_at.desc())
        .all()
    )

    latest_snapshots = {}
    for s in snapshots:
        if s.task_id not in latest_snapshots:
            latest_snapshots[s.task_id] = s

    result_tasks = []
    total_score = 0.0
    count = 0

    now = datetime.now(timezone.utc)

    for task_id, snap in latest_snapshots.items():
        task = task_map[task_id]

        # Calculate days remaining
        days_remaining = 0
        if task.due_date:
            delta = task.due_date - now
            days_remaining = delta.days

        total_score += snap.risk_score
        count += 1

        assignee_name = "Unassigned"
        # Tránh N+1 hoặc lỗi lazy load assignees bằng cách get assignees manually or just skip it if it throws
        try:
            if task.assignees and len(task.assignees) > 0 and task.assignees[0].user:
                assignee_name = task.assignees[0].user.name
        except Exception:
            pass

        result_tasks.append(
            {
                "task_id": task.id,
                "title": task.title,
                "assignee_name": assignee_name,
                "estimated_hours": task.estimated_hours or 0,
                "actual_hours": task.actual_hours or 0,
                "days_remaining": days_remaining,
                "risk_score": snap.risk_score,
                "risk_level": snap.risk_level,
                "recommendation": snap.recommendation,
                "signals": snap.signals,
                "created_at": snap.created_at.isoformat() if snap.created_at else None,
            }
        )

    overall_risk = (total_score / count) if count > 0 else 0.0

    return ResponseSchema(
        data={"overall_risk_index": overall_risk, "tasks": result_tasks},
        message="Risk stats fetched successfully",
    )


@router.get("/recent-updates", response_model=ResponseSchema[list[dict]])
def get_recent_status_updates(
    project_id: str,
    limit: int = Query(default=10, ge=1, le=50),
    current_user: User = Depends(get_current_active_user),
    db=Depends(get_db),
):
    """
    Lấy danh sách các cập nhật trạng thái gần đây của dự án.
    Trộn với bảng Task, User, TaskStatus để trả về dữ liệu hiển thị.
    """
    activities = (
        db.query(TaskActivity)
        .join(Task, Task.id == TaskActivity.task_id)
        .filter(Task.project_id == project_id)
        .options(joinedload(TaskActivity.task), joinedload(TaskActivity.user))
        .order_by(TaskActivity.created_at.desc())
        .limit(limit)
        .all()
    )

    results = []

    # Pre-fetch status names and colors to avoid N+1 queries
    status_ids = set()
    for activity in activities:
        if activity.old_value:
            status_ids.add(activity.old_value)
        if activity.new_value:
            status_ids.add(activity.new_value)

    status_map = {}
    if status_ids:
        statuses = db.query(TaskStatus).filter(TaskStatus.id.in_(status_ids)).all()
        status_map = {s.id: {"name": s.name, "color": s.color} for s in statuses}

    for activity in activities:
        old_status = (
            status_map.get(activity.old_value, {}) if activity.old_value else {}
        )
        new_status = (
            status_map.get(activity.new_value, {}) if activity.new_value else {}
        )

        results.append(
            {
                "id": activity.id,
                "task_id": activity.task_id,
                "task_title": activity.task.title if activity.task else "Unknown Task",
                "user_id": activity.user_id,
                "user_name": activity.user.name if activity.user else "System",
                "field_changed": activity.field_changed,
                "old_value": activity.old_value,
                "new_value": activity.new_value,
                "old_status_name": old_status.get("name"),
                "old_status_color": old_status.get("color"),
                "new_status_name": new_status.get("name"),
                "new_status_color": new_status.get("color"),
                "created_at": activity.created_at.isoformat()
                if activity.created_at
                else None,
            }
        )

    return ResponseSchema(data=results, message="Recent updates fetched successfully")


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
    result = service.patch(task_id, schema, user_id=current_user.id)
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
