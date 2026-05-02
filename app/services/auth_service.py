from uuid import uuid4

from app.core.exceptions import AuthError, DuplicatedError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_jwt,
    get_password_hash,
    verify_password,
)
from app.model.user import User
from app.repository.user_repository import UserRepository
from app.schema.auth_schema import (
    RefreshTokenRequest,
    SignIn,
    SignInResponse,
    SignUp,
    TokenResponse,
    UserInfo,
)
from app.schema.user_schema import UserCreateDB
from app.schema.team_schema import TeamCreate
from app.schema.project_schema import ProjectCreate
from app.services.user_service import UserService
from app.services.team_service import TeamService
from app.services.project_service import ProjectService
from app.services.calendar_service import CalendarService
from app.services.schedule_service import ScheduleService


class AuthService:
    def __init__(
        self,
        user_repository: UserRepository,
        user_service: UserService,
        team_service: TeamService,
        project_service: ProjectService,
        calendar_service: CalendarService,
        schedule_service: ScheduleService,
    ) -> None:
        self._user_repository = user_repository
        self._user_service = user_service
        self._team_service = team_service
        self._project_service = project_service
        self._calendar_service = calendar_service
        self._schedule_service = schedule_service

    def sign_up(self, schema: SignUp) -> UserInfo:
        existing_user = self._user_repository.read_by_email(str(schema.email))
        if existing_user:
            raise DuplicatedError(detail="Email already exists.")

        user_schema = UserCreateDB(
            email=schema.email,
            name=schema.name,
            avatar_url=schema.avatar_url,
            hashed_password=get_password_hash(schema.password),
            user_token=uuid4().hex,
        )
        
        try:
            # Create user without committing
            user = self._user_repository.create(user_schema, auto_commit=False)

            # Create default team without committing
            team_create = TeamCreate(
                name=f"{user.name}'s Team",
                description=f"Default team for {user.name}"
            )
            team = self._team_service.create_team(team_create, user, auto_commit=False)

            # Create default project without committing
            project_create = ProjectCreate(
                team_id=team.id,
                name=f"{user.name}'s Project",
                description=f"Default project for {user.name}",
            )
            self._project_service.create_project(project_create, user)

            # Create personal and team calendars
            self._calendar_service.get_or_create_personal_calendar(user.id, user.name)
            self._calendar_service.get_or_create_team_calendar(team.id, team.name)

            # Create default personal schedule for the user
            self._schedule_service.create_default_user_schedule(user.id)

            # Manual commit for the entire transaction
            self._user_repository.commit()
            
            return self._user_service.to_user_info(user)
        except Exception as e:
            # In case of any error, we don't commit. 
            # SQLAlchemy session from get_db will handle rollback on exception.
            raise e

    def sign_in(self, schema: SignIn) -> SignInResponse:
        user = self._user_repository.read_by_email(str(schema.email__eq))
        if not user:
            raise AuthError(detail="Email does not exist.")

        if not user.is_active:
            raise AuthError(detail="User is inactive.")

        if not verify_password(schema.password, user.hashed_password):
            raise AuthError(detail="Incorrect password.")

        subject = {
            "sub": str(user.id),
            "email": user.email,
            "name": user.name,
        }
        access_token, expiration = create_access_token(subject)
        refresh_token, refresh_expiration = create_refresh_token(subject)

        user_info = self._user_service.to_user_info(user)

        return SignInResponse(
            access_token=access_token,
            expiration=expiration,
            refresh_token=refresh_token,
            refresh_expiration=refresh_expiration,
            user_info=user_info,
        )

    def refresh_token(self, payload: RefreshTokenRequest) -> TokenResponse:
        decoded = decode_jwt(payload.refresh_token)
        if not decoded or decoded.get("type") != "refresh":
            raise AuthError(detail="Invalid refresh token.")

        user_id = decoded.get("sub")
        if not user_id:
            raise AuthError(detail="Invalid token payload.")

        user = self._user_repository.read_by_id(user_id)
        if not user:
            raise AuthError(detail="User not found.")

        if not user.is_active:
            raise AuthError(detail="User is inactive.")

        subject = {
            "sub": str(user.id),
            "email": user.email,
            "name": user.name,
        }
        access_token, expiration = create_access_token(subject)
        refresh_token, refresh_expiration = create_refresh_token(subject)

        return TokenResponse(
            access_token=access_token,
            expiration=expiration,
            refresh_token=refresh_token,
            refresh_expiration=refresh_expiration,
        )
