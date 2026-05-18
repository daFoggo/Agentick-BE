from app.core.exceptions import AuthError, NotFoundError
from app.repository.project_member_repository import ProjectMemberRepository
from app.repository.project_repository import ProjectRepository
from app.repository.task_repository import TaskRepository
from app.repository.team_member_repository import TeamMemberRepository
from app.schema.project_member_schema import ProjectMemberFind
from app.schema.team_member_schema import TeamMemberFind


PROJECT_READ_ROLES = {"owner", "manager", "member", "viewer"}
PROJECT_TASK_WRITE_ROLES = {"owner", "manager", "member"}
PROJECT_MANAGE_ROLES = {"owner", "manager"}


class ProjectPermissionService:
    def __init__(
        self,
        project_repository: ProjectRepository,
        project_member_repository: ProjectMemberRepository,
        team_member_repository: TeamMemberRepository,
        task_repository: TaskRepository | None = None,
    ) -> None:
        self._project_repository = project_repository
        self._project_member_repository = project_member_repository
        self._team_member_repository = team_member_repository
        self._task_repository = task_repository

    def _get_project_or_raise(self, project_id: str):
        project = self._project_repository.read_by_id(project_id)
        if not project or project.is_deleted:
            raise NotFoundError(detail="Project not found.")
        return project

    def get_project_role(self, project_id: str, user_id: str) -> str | None:
        member = self._project_member_repository.read_by_options(
            ProjectMemberFind(project_id__eq=project_id, user_id__eq=user_id)
        )
        members = member.get("founds", [])
        return members[0].role if members else None

    def get_team_role(self, team_id: str, user_id: str) -> str | None:
        member = self._team_member_repository.read_by_options(
            TeamMemberFind(team_id__eq=team_id, user_id__eq=user_id)
        )
        members = member.get("founds", [])
        return members[0].role if members else None

    def ensure_project_read(self, project_id: str, user_id: str):
        project = self._get_project_or_raise(project_id)
        role = self.get_project_role(project_id, user_id)
        if role not in PROJECT_READ_ROLES:
            raise AuthError(detail="You are not a member of this project.")
        return project

    def ensure_project_task_write(self, project_id: str, user_id: str):
        project = self.ensure_project_read(project_id, user_id)
        role = self.get_project_role(project_id, user_id)
        if role not in PROJECT_TASK_WRITE_ROLES:
            raise AuthError(detail="Insufficient privileges to manage tasks.")
        return project

    def ensure_project_manage(self, project_id: str, user_id: str):
        project = self.ensure_project_read(project_id, user_id)
        role = self.get_project_role(project_id, user_id)
        if role not in PROJECT_MANAGE_ROLES:
            raise AuthError(detail="Insufficient privileges to manage this project.")
        return project

    def ensure_project_manage_or_team_manager(self, project_id: str, user_id: str):
        project = self._get_project_or_raise(project_id)
        project_role = self.get_project_role(project_id, user_id)
        team_role = self.get_team_role(project.team_id, user_id)
        if project_role in PROJECT_MANAGE_ROLES or team_role in PROJECT_MANAGE_ROLES:
            return project
        raise AuthError(detail="Insufficient privileges to manage this project.")

    def ensure_task_read(self, task_id: str, user_id: str):
        task = self._get_task_or_raise(task_id)
        self.ensure_project_read(task.project_id, user_id)
        return task

    def ensure_task_write(self, task_id: str, user_id: str):
        task = self._get_task_or_raise(task_id)
        self.ensure_project_task_write(task.project_id, user_id)
        return task

    def _get_task_or_raise(self, task_id: str):
        if self._task_repository is None:
            raise RuntimeError("Task repository is required for task permissions.")
        task = self._task_repository.read_by_id(task_id, eager=True)
        if not task or task.is_deleted:
            raise NotFoundError(detail="Task not found.")
        return task
