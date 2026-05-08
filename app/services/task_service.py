from typing import Any
from app.services.base_service import BaseService


class TaskService(BaseService):
    def __init__(self, repository: Any) -> None:
        super().__init__(repository)

    def add(self, schema: Any) -> Any:
        result = super().add(schema)
        if hasattr(schema, "assignee_ids") and schema.assignee_ids:
            with self._repository.session_factory() as session:
                from app.model.project_member import ProjectMember
                from app.model.project import Project
                from app.model.team import Team
                from app.model.notification import Notification, NotificationType, NotificationStatus

                project = session.query(Project).filter_by(id=result.project_id).first()
                team = session.query(Team).filter_by(id=project.team_id).first() if project else None

                members = session.query(ProjectMember).filter(ProjectMember.id.in_(schema.assignee_ids)).all()
                for member in members:
                    notification = Notification(
                        user_id=member.user_id,
                        title="New Task Assigned",
                        content=f"You have been assigned to task '{result.title}' in project '{project.name if project else 'Unknown'}' ({team.name if team else 'Unknown Team'})",
                        type=NotificationType.TASK_ASSIGNED,
                        status=NotificationStatus.ACTIVE,
                        is_read=False,
                        resource_id=result.id,
                        resource_type="task",
                        data={
                            "task_id": result.id,
                            "task_title": result.title,
                            "project_id": result.project_id,
                            "project_name": project.name if project else None,
                            "team_id": project.team_id if project else None,
                            "team_name": team.name if team else None,
                        }
                    )
                    session.add(notification)
                session.commit()
        return result

    def patch(self, id: str, schema: Any) -> Any:
        old_assignee_ids = set()
        with self._repository.session_factory() as session:
            old_task = session.query(self._repository.model).filter_by(id=id).first()
            if old_task:
                old_assignee_ids = {a.id for a in old_task.assignees}
                
        result = super().patch(id, schema)
        
        if hasattr(schema, "assignee_ids") and schema.assignee_ids is not None:
            new_assignee_ids = set(schema.assignee_ids)
            added_ids = new_assignee_ids - old_assignee_ids
            if added_ids:
                with self._repository.session_factory() as session:
                    from app.model.project_member import ProjectMember
                    from app.model.project import Project
                    from app.model.team import Team
                    from app.model.notification import Notification, NotificationType, NotificationStatus

                    project = session.query(Project).filter_by(id=result.project_id).first()
                    team = session.query(Team).filter_by(id=project.team_id).first() if project else None

                    members = session.query(ProjectMember).filter(ProjectMember.id.in_(added_ids)).all()
                    for member in members:
                        notification = Notification(
                            user_id=member.user_id,
                            title="New Task Assigned",
                            content=f"You have been assigned to task '{result.title}' in project '{project.name if project else 'Unknown'}' ({team.name if team else 'Unknown Team'})",
                            type=NotificationType.TASK_ASSIGNED,
                            status=NotificationStatus.ACTIVE,
                            is_read=False,
                            resource_id=result.id,
                            resource_type="task",
                            data={
                                "task_id": result.id,
                                "task_title": result.title,
                                "project_id": result.project_id,
                                "project_name": project.name if project else None,
                                "team_id": project.team_id if project else None,
                                "team_name": team.name if team else None,
                            }
                        )
                        session.add(notification)
                    session.commit()
        return result

    def patch_attr(self, id: str, attr: str, value: Any) -> Any:
        return super().patch_attr(id, attr, value)

    def get_gantt_data(self, project_id: str):
        """
        Fetches all tasks for a project, including phase and assignee info.
        """
        # Using read_by_options with eager=True to get status, phase, assignee
        result = self._repository.read_by_options(
            {"project_id__eq": project_id, "is_deleted__eq": False, "page_size": "all"},
            eager=True,
        )
        return result["founds"]
