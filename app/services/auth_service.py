from uuid import uuid4

from app.core.exceptions import AuthError, DuplicatedError
from app.core.security import create_access_token, get_password_hash, verify_password
from app.model.user import User
from app.repository.user_repository import UserRepository
from app.schema.auth_schema import SignIn, SignInResponse, SignUp, UserInfo
from app.schema.user_schema import UserCreateDB


class AuthService:
    def __init__(self, user_repository: UserRepository) -> None:
        self._user_repository = user_repository

    @staticmethod
    def _to_user_info(user: User) -> UserInfo:
        return UserInfo(
            id=str(user.id),
            name=user.name,
            email=user.email,
            avatarUrl=user.avatar_url,
            createdAt=user.created_at,
        )

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
        return self._to_user_info(user)

    def sign_in(self, schema: SignIn) -> SignInResponse:
        user = self._user_repository.read_by_email(str(schema.email__eq))
        if not user:
            raise AuthError(detail="Email does not exist.")

        if not user.is_active:
            raise AuthError(detail="User is inactive.")

        if not verify_password(schema.password, user.hashed_password):
            raise AuthError(detail="Incorrect password.")

        access_token, expiration = create_access_token(
            {
                "sub": str(user.id),
                "email": user.email,
                "name": user.name,
            }
        )
        return SignInResponse(
            access_token=access_token,
            expiration=expiration,
            user_info=self._to_user_info(user),
        )
