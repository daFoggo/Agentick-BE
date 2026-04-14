from contextlib import AbstractContextManager
from typing import Callable

from sqlalchemy.orm import Session

from app.model.team_member import TeamMember
from app.repository.base_repository import BaseRepository


class TeamMemberRepository(BaseRepository):
    def __init__(self, session_factory: Callable[..., AbstractContextManager[Session]]) -> None:
        super().__init__(session_factory=session_factory, model=TeamMember)

    def search_members(self, team_id: str, q: str, page: int = 1, page_size: int = 20):
        with self.session_factory() as session:
            from app.model.user import User
            from sqlalchemy.orm import joinedload
            
            query = (
                session.query(self.model)
                .join(User, User.id == self.model.user_id)
                .filter(self.model.team_id == team_id)
                .filter(
                    (User.name.ilike(f"%{q}%")) | (User.email.ilike(f"%{q}%"))
                )
            )
            
            total_count = query.count()
            
            # Eager load user profile
            results = query.options(joinedload(self.model.user)).limit(page_size).offset((page - 1) * page_size).all()
            
            return {
                "founds": results,
                "search_options": {
                    "page": page,
                    "page_size": page_size,
                    "total_count": total_count,
                }
            }
