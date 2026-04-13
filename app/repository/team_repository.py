from contextlib import AbstractContextManager
from typing import Callable

from sqlalchemy.orm import Session

from app.model.team import Team
from app.model.team_member import TeamMember
from app.repository.base_repository import BaseRepository


class TeamRepository(BaseRepository):
    def __init__(self, session_factory: Callable[..., AbstractContextManager[Session]]) -> None:
        super().__init__(session_factory=session_factory, model=Team)

    def get_my_teams(self, user_id: str):
        with self.session_factory() as session:
            query = (
                session.query(self.model)
                .join(TeamMember)
                .filter(TeamMember.user_id == user_id, Team.is_deleted == False)
            )
            return query.all()
