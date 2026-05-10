from contextlib import AbstractContextManager
from typing import Callable

from sqlalchemy.orm import Session

from app.model.project import Project
from app.model.project_member import ProjectMember
from app.repository.base_repository import BaseRepository


class ProjectRepository(BaseRepository):
    def __init__(
        self, session_factory: Callable[..., AbstractContextManager[Session]]
    ) -> None:
        super().__init__(session_factory=session_factory, model=Project)

    def get_my_projects(self, user_id: str, team_id: str = None):
        with self.session_factory() as session:
            query = (
                session.query(self.model)
                .join(ProjectMember, ProjectMember.project_id == Project.id)
                .filter(ProjectMember.user_id == user_id, Project.is_deleted.is_(False))
            )
            if team_id:
                query = query.filter(Project.team_id == team_id)
            return query.all()

    def cleanup_project_resources_on_delete(self, project_id: str):
        from app.model.task import Task
        from app.model.event import Event

        with self.session_factory() as session:
            tasks = (
                session.query(Task)
                .filter(Task.project_id == project_id, Task.is_deleted.is_(False))
                .all()
            )
            for task in tasks:
                task.is_deleted = True
                session.query(Event).filter(Event.task_id == task.id).delete(
                    synchronize_session=False
                )
            session.commit()
