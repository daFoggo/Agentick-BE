from contextlib import nullcontext
from typing import Literal

from fastapi import APIRouter, Depends, Query

from app.core.dependencies import get_db, get_current_active_user
from app.model.user import User
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
    project_member_repository = ProjectMemberRepository(lambda: nullcontext(db))
    return TaskService(
        repository=task_repository, project_member_repo=project_member_repository
    )


def get_user_service(db=Depends(get_db)) -> UserService:
    user_repository = UserRepository(lambda: nullcontext(db))
    team_member_repository = TeamMemberRepository(lambda: nullcontext(db))
    project_member_repository = ProjectMemberRepository(lambda: nullcontext(db))
    task_repository = TaskRepository(lambda: nullcontext(db))
    return UserService(
        user_repository=user_repository,
        team_member_repository=team_member_repository,
        project_member_repository=project_member_repository,
        task_repository=task_repository,
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
    service: TaskService = Depends(get_task_service),
):
    """Lấy danh sách task liên quan đến current user (assignee hoặc assigner)."""
    results = service.get_my_tasks(
        user_id=current_user.id,
        team_id=find_query.team_id__eq,
    )

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
    service: UserService = Depends(get_user_service),
):
    """Thống kê cá nhân: số task hoàn thành và số người cộng tác trong tuần/tháng."""
    result = service.get_user_stats(user_id=current_user.id, period=period)
    return ResponseSchema(
        data=result,
        message="User stats fetched successfully",
    )
