from app.model.user import User
from app.repository.user_repository import UserRepository
from app.schema.auth_schema import UserInfo


class UserService:
    def __init__(self, user_repository: UserRepository) -> None:
        self._user_repository = user_repository

    @staticmethod
    def to_user_info(user: User) -> UserInfo:
        return UserInfo.model_validate(user)

    def get_me(self, user: User) -> UserInfo:
        return self.to_user_info(user)
