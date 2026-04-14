from contextlib import AbstractContextManager
from typing import Callable

from sqlalchemy.orm import Session

from app.model.project import Project
from app.model.team_member import TeamMember
from app.repository.base_repository import BaseRepository


class ProjectRepository(BaseRepository):
    def __init__(self, session_factory: Callable[..., AbstractContextManager[Session]]) -> None:
        super().__init__(session_factory=session_factory, model=Project)

    def get_my_projects(self, user_id: str):
        with self.session_factory() as session:
            query = (
                session.query(self.model)
                .join(TeamMember, TeamMember.team_id == Project.team_id)
                .filter(TeamMember.user_id == user_id, Project.is_deleted == False)
            )
            return query.all()
