from contextlib import AbstractContextManager
from typing import Callable

from sqlalchemy.orm import Session

from app.model.project import Project
from app.model.project_member import ProjectMember
from app.repository.base_repository import BaseRepository

class ProjectRepository(BaseRepository):
    def __init__(self, session_factory: Callable[..., AbstractContextManager[Session]]) -> None:
        super().__init__(session_factory=session_factory, model=Project)

    def get_my_projects(self, user_id: str, team_id: str = None):
        with self.session_factory() as session:
            query = (
                session.query(self.model)
                .join(ProjectMember, ProjectMember.project_id == Project.id)
                .filter(ProjectMember.user_id == user_id, Project.is_deleted == False)
            )
            if team_id:
                query = query.filter(Project.team_id == team_id)
            return query.all()
