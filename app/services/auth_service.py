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
from app.services.user_service import UserService


class AuthService:
    def __init__(self, user_repository: UserRepository, user_service: UserService) -> None:
        self._user_repository = user_repository
        self._user_service = user_service

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
        user = self._user_repository.create(user_schema)
        return self._user_service.to_user_info(user)

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

        return SignInResponse(
            access_token=access_token,
            expiration=expiration,
            refresh_token=refresh_token,
            refresh_expiration=refresh_expiration,
            user_info=self._user_service.to_user_info(user),
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
