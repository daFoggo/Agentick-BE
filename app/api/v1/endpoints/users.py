from contextlib import nullcontext
from fastapi import APIRouter, Depends

from app.core.dependencies import get_db, get_current_active_user
from app.model.user import User
from app.repository.user_repository import UserRepository
from app.repository.team_member_repository import TeamMemberRepository
from app.schema.base_schema import ResponseSchema
from app.schema.auth_schema import UserInfo
from app.schema.user_schema import UserSearch, UserSearchResult
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["users"])


def get_user_service(db=Depends(get_db)) -> UserService:
    user_repository = UserRepository(lambda: nullcontext(db))
    team_member_repository = TeamMemberRepository(lambda: nullcontext(db))
    return UserService(
        user_repository=user_repository,
        team_member_repository=team_member_repository,
    )


@router.get("/me", response_model=ResponseSchema[UserInfo])
def get_me(user: User = Depends(get_current_active_user), service: UserService = Depends(get_user_service)):
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
        team_id=search_query.team_id,
    )
    return ResponseSchema(data=results, message="Users found")
