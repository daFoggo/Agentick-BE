from contextlib import nullcontext
from fastapi import APIRouter, Depends

from app.core.dependencies import get_db
from app.repository.user_repository import UserRepository
from app.repository.team_repository import TeamRepository
from app.repository.team_member_repository import TeamMemberRepository
from app.repository.project_repository import ProjectRepository
from app.repository.project_member_repository import ProjectMemberRepository
from app.schema.base_schema import ResponseSchema
from app.schema.auth_schema import RefreshTokenRequest, SignIn, SignInResponse, SignUp, TokenResponse, UserInfo
from app.services.auth_service import AuthService
from app.services.user_service import UserService
from app.services.team_service import TeamService
from app.services.project_service import ProjectService

router = APIRouter(prefix="/auth", tags=["auth"])


def get_auth_service(db=Depends(get_db)) -> AuthService:
    user_repository = UserRepository(lambda: nullcontext(db))
    user_service = UserService(user_repository=user_repository)
    team_repository = TeamRepository(lambda: nullcontext(db))
    team_member_repository = TeamMemberRepository(lambda: nullcontext(db))
    team_service = TeamService(team_repository=team_repository, team_member_repository=team_member_repository)
    project_repository = ProjectRepository(lambda: nullcontext(db))
    project_member_repository = ProjectMemberRepository(lambda: nullcontext(db))
    project_service = ProjectService(
        project_repository=project_repository,
        team_repository=team_repository,
        team_member_repository=team_member_repository,
        project_member_repository=project_member_repository,
    )
    return AuthService(
        user_repository=user_repository,
        user_service=user_service,
        team_service=team_service,
        project_service=project_service,
    )


@router.post("/sign-up", response_model=ResponseSchema[UserInfo])
def sign_up(payload: SignUp, service: AuthService = Depends(get_auth_service)):
    result = service.sign_up(payload)
    return ResponseSchema(data=result, message="User registered successfully")


@router.post("/sign-in", response_model=ResponseSchema[SignInResponse])
def sign_in(payload: SignIn, service: AuthService = Depends(get_auth_service)):
    result = service.sign_in(payload)
    return ResponseSchema(data=result, message="Login successful")


@router.post("/refresh", response_model=ResponseSchema[TokenResponse])
def refresh_token(payload: RefreshTokenRequest, service: AuthService = Depends(get_auth_service)):
    result = service.refresh_token(payload)
    return ResponseSchema(data=result, message="Token refreshed successfully")
