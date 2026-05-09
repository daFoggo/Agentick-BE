from contextlib import nullcontext
from datetime import datetime, timedelta, timezone
from typing import Literal

from fastapi import APIRouter, Depends, Query

from app.core.dependencies import get_db, get_current_active_user
from app.model.user import User
from app.model.task import Task, task_assignee
from app.model.task_status import TaskStatus
from app.model.project_member import ProjectMember
from app.repository.user_repository import UserRepository
from app.repository.team_member_repository import TeamMemberRepository
from app.repository.project_member_repository import ProjectMemberRepository
from app.repository.task_repository import TaskRepository
from app.schema.base_schema import FindResult, ResponseSchema
from app.schema.auth_schema import UserInfo
from app.schema.user_schema import UserSearch, UserSearchResult
from app.schema.task_schema import TaskFind, TaskRead
from app.services.user_service import UserService
from app.services.task_service import TaskService

router = APIRouter(prefix="/users", tags=["users"])


def get_task_service(db=Depends(get_db)) -> TaskService:
    task_repository = TaskRepository(lambda: nullcontext(db))
    return TaskService(repository=task_repository)


def get_user_service(db=Depends(get_db)) -> UserService:
    user_repository = UserRepository(lambda: nullcontext(db))
    team_member_repository = TeamMemberRepository(lambda: nullcontext(db))
    project_member_repository = ProjectMemberRepository(lambda: nullcontext(db))
    return UserService(
        user_repository=user_repository,
        team_member_repository=team_member_repository,
        project_member_repository=project_member_repository,
    )


@router.get("/me", response_model=ResponseSchema[UserInfo])
def get_me(
    user: User = Depends(get_current_active_user),
    service: UserService = Depends(get_user_service),
):
    result = service.get_me(user)
    return ResponseSchema(data=result, message="User profile fetched successfully")


@router.get("/search", response_model=ResponseSchema[list[UserSearchResult]])
def search_users(
    search_query: UserSearch = Depends(),
    current_user: User = Depends(get_current_active_user),
    service: UserService = Depends(get_user_service),
):
    """Search users by email or name — for team invite flow"""
    results = service.search_users(
        query=search_query.q,
        limit=search_query.limit,
        exclude_user_ids=[current_user.id],
        exclude_team_id=search_query.exclude_team_id,
        exclude_project_id=search_query.exclude_project_id,
    )
    return ResponseSchema(data=results, message="Users found")


@router.get("/me/tasks", response_model=ResponseSchema[FindResult[TaskRead]])
def get_my_tasks(
    find_query: TaskFind = Depends(),
    current_user: User = Depends(get_current_active_user),
    db=Depends(get_db),
):
    """Lấy danh sách task liên quan đến current user (assignee hoặc assigner)."""
    from sqlalchemy import or_
    from sqlalchemy.orm import joinedload

    query = db.query(Task).filter(
        Task.is_deleted.is_(False), Task.is_archived.is_(False)
    )

    user_member_ids = [
        row[0]
        for row in db.query(ProjectMember.id)
        .filter(ProjectMember.user_id == current_user.id)
        .all()
    ]

    if user_member_ids:
        query = query.filter(
            or_(
                Task.assignees.any(ProjectMember.user_id == current_user.id),
                Task.assigner_id.in_(user_member_ids),
            )
        )
    else:
        return ResponseSchema(
            data={
                "founds": [],
                "search_options": {
                    "page": 1,
                    "page_size": "all",
                    "ordering": "-id",
                    "total_count": 0,
                },
            },
            message="My tasks fetched successfully",
        )

    for eager_attr in Task.eagers:
        query = query.options(joinedload(getattr(Task, eager_attr)))

    results = query.order_by(Task.id.desc()).all()

    return ResponseSchema(
        data={
            "founds": results,
            "search_options": {
                "page": 1,
                "page_size": "all",
                "ordering": "-id",
                "total_count": len(results),
            },
        },
        message="My tasks fetched successfully",
    )


@router.get("/me/stats", response_model=ResponseSchema[dict])
def get_my_stats(
    period: Literal["weekly", "monthly"] = Query(default="weekly"),
    current_user: User = Depends(get_current_active_user),
    db=Depends(get_db),
):
    """Thống kê cá nhân: số task hoàn thành và số người cộng tác trong tuần/tháng."""
    now = datetime.now(timezone.utc)
    delta = timedelta(days=7) if period == "weekly" else timedelta(days=30)
    since = now - delta

    # Lấy tất cả ProjectMember ID của user này (có thể là member nhiều project)
    user_member_ids = [
        row[0]
        for row in db.query(ProjectMember.id)
        .filter(ProjectMember.user_id == current_user.id)
        .all()
    ]

    if not user_member_ids:
        return ResponseSchema(
            data={"tasks_completed": 0, "collaborated_with": 0, "period": period},
            message="User stats fetched successfully",
        )

    # Query: task_id của các task được assign cho user
    # Không dùng .subquery() — truyền thẳng query object vào .in_() để tránh SAWarning
    user_task_ids_q = db.query(task_assignee.c.task_id).filter(
        task_assignee.c.project_member_id.in_(user_member_ids)
    )

    # --- 1. tasks_completed ---
    # Task được assign cho user, status is_completed=True, được cập nhật trong period
    tasks_completed = (
        db.query(Task)
        .join(TaskStatus, TaskStatus.id == Task.status_id)
        .filter(
            Task.id.in_(user_task_ids_q),
            TaskStatus.is_completed.is_(True),
            Task.updated_at >= since,
            Task.is_deleted.is_(False),
        )
        .count()
    )

    # --- 2. collaborated_with ---
    # Query: task_id của user được cập nhật trong period
    active_task_ids_q = db.query(Task.id).filter(
        Task.id.in_(user_task_ids_q),
        Task.updated_at >= since,
        Task.is_deleted.is_(False),
    )

    # Lấy project_member_id khác (không phải của user hiện tại) trên các task active
    other_member_ids_q = (
        db.query(task_assignee.c.project_member_id)
        .filter(
            task_assignee.c.task_id.in_(active_task_ids_q),
            task_assignee.c.project_member_id.not_in(user_member_ids),
        )
        .distinct()
    )

    # Đếm distinct user_id từ các project_member khác đó
    collaborated_with = (
        db.query(ProjectMember.user_id)
        .filter(ProjectMember.id.in_(other_member_ids_q))
        .distinct()
        .count()
    )

    return ResponseSchema(
        data={
            "tasks_completed": tasks_completed,
            "collaborated_with": collaborated_with,
            "period": period,
        },
        message="User stats fetched successfully",
    )
