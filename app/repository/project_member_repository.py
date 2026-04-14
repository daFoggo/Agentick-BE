from contextlib import AbstractContextManager
from typing import Callable

from sqlalchemy.orm import Session

from app.model.project_member import ProjectMember
from app.repository.base_repository import BaseRepository


class ProjectMemberRepository(BaseRepository):
    def __init__(self, session_factory: Callable[..., AbstractContextManager[Session]]) -> None:
        super().__init__(session_factory=session_factory, model=ProjectMember)

    def remove_from_all_team_projects(self, team_id: str, user_id: str):
        with self.session_factory() as session:
            from app.model.project import Project
            
            # Find all project IDs belonging to this team
            project_ids_subquery = session.query(Project.id).filter(Project.team_id == team_id).subquery()
            
            # Delete project member records for these projects and this user
            session.query(self.model).filter(
                self.model.user_id == user_id,
                self.model.project_id.in_(project_ids_subquery)
            ).delete(synchronize_session=False)
            
            session.commit()

    def count_projects_in_team(self, team_id: str, user_id: str) -> int:
        with self.session_factory() as session:
            from app.model.project import Project
            
            count = (
                session.query(self.model)
                .join(Project, Project.id == self.model.project_id)
                .filter(Project.team_id == team_id, self.model.user_id == user_id)
                .count()
            )
            return count
