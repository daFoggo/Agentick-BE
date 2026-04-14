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

    def search_users(
        self,
        query: str,
        limit: int = 10,
        exclude_user_ids: list[str] | None = None,
    ) -> list[User]:
        """
        Search users by email or name using pg_trgm similarity.
        GIN trigram indexes on email/name ensures fast lookups up to ~1M users.
        """
        with self.session_factory() as session:
            from sqlalchemy import or_, func

            search_pattern = f"%{query}%"
            q = session.query(self.model).filter(
                or_(
                    self.model.email.ilike(search_pattern),
                    self.model.name.ilike(search_pattern),
                ),
                self.model.is_active == True,  # noqa: E712
            )

            if exclude_user_ids:
                q = q.filter(self.model.id.notin_(exclude_user_ids))

            # Order by best trigram similarity match
            q = q.order_by(
                func.greatest(
                    func.similarity(self.model.email, query),
                    func.similarity(self.model.name, query),
                ).desc()
            )

            return q.limit(limit).all()
