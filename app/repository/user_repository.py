from contextlib import AbstractContextManager
from typing import Callable

from sqlalchemy.orm import Session

from app.model.user import User
from app.repository.base_repository import BaseRepository
from app.schema.user_schema import UserFind


class UserRepository(BaseRepository):
    def __init__(self, session_factory: Callable[..., AbstractContextManager[Session]]) -> None:
        super().__init__(session_factory=session_factory, model=User)

    def read_by_email(self, email: str) -> User | None:
        search_schema = UserFind(email__eq=email)
        result = self.read_by_options(search_schema)
        users: list[User] = result.get("founds", [])
        return users[0] if users else None
