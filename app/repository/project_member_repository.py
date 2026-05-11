from contextlib import AbstractContextManager
from typing import Callable

from sqlalchemy.orm import Session

from app.model.project_member import ProjectMember
from app.repository.base_repository import BaseRepository


class ProjectMemberRepository(BaseRepository):
    def __init__(
        self, session_factory: Callable[..., AbstractContextManager[Session]]
    ) -> None:
        super().__init__(session_factory=session_factory, model=ProjectMember)

    def remove_from_all_team_projects(self, team_id: str, user_id: str):
        with self.session_factory() as session:
            from app.model.project import Project

            # Find all project IDs belonging to this team
            project_ids_subquery = (
                session.query(Project.id)
                .filter(Project.team_id == team_id, Project.is_deleted.is_(False))
                .subquery()
            )

            # Delete project member records for these projects and this user
            session.query(self.model).filter(
                self.model.user_id == user_id,
                self.model.project_id.in_(project_ids_subquery),
            ).delete(synchronize_session=False)

            session.commit()

    def count_projects_in_team(self, team_id: str, user_id: str) -> int:
        with self.session_factory() as session:
            from app.model.project import Project

            count = (
                session.query(self.model)
                .join(Project, Project.id == self.model.project_id)
                .filter(
                    Project.team_id == team_id,
                    self.model.user_id == user_id,
                    Project.is_deleted.is_(False),
                )
                .count()
            )
            return count

    def get_member_ids_by_user(self, user_id: str) -> list[str]:
        with self.session_factory() as session:
            from app.model.project import Project

            return [
                row[0]
                for row in session.query(self.model.id)
                .join(Project, self.model.project_id == Project.id)
                .filter(
                    self.model.user_id == user_id,
                    Project.is_deleted.is_(False),
                )
                .all()
            ]

    def get_member_workload_raw(self, project_id: str, date_from, date_to):
        with self.session_factory() as session:
            from sqlalchemy import func, distinct, cast, Date as SADate
            from sqlalchemy.orm import joinedload
            from app.model.task import Task
            from app.model.task_status import TaskStatus

            # 1. Fetch project members with users preloaded
            members = (
                session.query(self.model)
                .options(joinedload(self.model.user))
                .filter(self.model.project_id == project_id)
                .all()
            )

            member_data = []

            # 2. For each member, execute the workload query
            from app.model.task_member import TaskMember

            for member in members:
                local_day_expr = cast(
                    func.timezone("Asia/Ho_Chi_Minh", Task.updated_at), SADate
                ).label("day")

                rows = (
                    session.query(
                        local_day_expr,
                        func.count(distinct(Task.id)).label("task_count"),
                    )
                    .join(TaskMember, TaskMember.task_id == Task.id)
                    .join(TaskStatus, Task.status_id == TaskStatus.id)
                    .filter(
                        Task.project_id == project_id,
                        TaskMember.user_id == member.user_id,
                        Task.is_deleted.is_(False),
                        Task.is_archived.is_(False),
                        (
                            TaskStatus.is_completed.is_(True)
                            | (func.lower(TaskStatus.name) == "done")
                        ),
                        Task.updated_at >= date_from,
                        Task.updated_at < date_to,
                    )
                    .group_by(local_day_expr)
                    .order_by(local_day_expr)
                    .all()
                )
                member_data.append((member, rows))

            return member_data
