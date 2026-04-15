from app.core.exceptions import AuthError, NotFoundError
from app.model.user import User
from app.repository.project_repository import ProjectRepository
from app.repository.project_member_repository import ProjectMemberRepository
from app.repository.team_member_repository import TeamMemberRepository
from app.repository.team_repository import TeamRepository
from app.repository.task_status_repository import TaskStatusRepository
from app.repository.task_type_repository import TaskTypeRepository
from app.repository.task_priority_repository import TaskPriorityRepository
from app.schema.project_schema import ProjectCreate, ProjectFind, ProjectUpdate
from app.schema.team_member_schema import TeamMemberFind
from app.services.base_service import BaseService


class ProjectService(BaseService):
    def __init__(
        self,
        project_repository: ProjectRepository,
        team_repository: TeamRepository,
        team_member_repository: TeamMemberRepository,
        project_member_repository: ProjectMemberRepository,
        task_status_repository: TaskStatusRepository,
        task_type_repository: TaskTypeRepository,
        task_priority_repository: TaskPriorityRepository,
    ) -> None:
        super().__init__(repository=project_repository)
        self._team_repository = team_repository
        self._team_member_repository = team_member_repository
        self._project_member_repository = project_member_repository
        self._task_status_repository = task_status_repository
        self._task_type_repository = task_type_repository
        self._task_priority_repository = task_priority_repository

    def _ensure_user_in_team(self, team_id: str, user_id: str, allow_roles: set[str] | None = None):
        team = self._team_repository.read_by_id(team_id)
        if not team or team.is_deleted:
            raise NotFoundError(detail="Team not found.")

        current_member = self._team_member_repository.read_by_options(
            TeamMemberFind(team_id__eq=team_id, user_id__eq=user_id)
        )
        if not current_member.get("founds"):
            raise AuthError(detail="You are not a member of this team.")

        role = current_member["founds"][0].role
        if allow_roles and role not in allow_roles:
            raise AuthError(detail="Insufficient privileges for this action.")

    def _seed_project_catalogs(self, project_id: str):
        """Seed default TaskStatus, TaskType, and TaskPriority for a new project."""
        def _mark_single_default(items: list[dict], default_index: int = 0, completed_index: int | None = None) -> list[dict]:
            normalized_items: list[dict] = []
            for index, item in enumerate(items):
                normalized_item = item.copy()
                normalized_item["is_default"] = index == default_index
                if completed_index is not None and "is_completed" in normalized_item:
                    normalized_item["is_completed"] = index == completed_index
                normalized_items.append(normalized_item)
            return normalized_items

        # Default Task Statuses
        statuses = _mark_single_default(
            [
                {"project_id": project_id, "name": "To Do", "color": "#808080", "order": 0, "is_completed": False},
                {"project_id": project_id, "name": "In Progress", "color": "#0066CC", "order": 1, "is_completed": False},
                {"project_id": project_id, "name": "In Review", "color": "#FF9900", "order": 2, "is_completed": False},
                {"project_id": project_id, "name": "Done", "color": "#00CC00", "order": 3, "is_completed": False},
            ],
            default_index=0,
            completed_index=3,
        )
        for status in statuses:
            self._task_status_repository.create(status)

        # Default Task Types
        types = _mark_single_default(
            [
                {"project_id": project_id, "name": "Feature", "color": "#0066CC", "icon": "star", "order": 0},
                {"project_id": project_id, "name": "Bug", "color": "#DD0000", "icon": "bug", "order": 1},
                {"project_id": project_id, "name": "Improvement", "color": "#FF9900", "icon": "zap", "order": 2},
                {"project_id": project_id, "name": "Task", "color": "#6600CC", "icon": "check", "order": 3},
            ],
            default_index=0,
        )
        for task_type in types:
            self._task_type_repository.create(task_type)

        # Default Task Priorities
        priorities = _mark_single_default(
            [
                {"project_id": project_id, "name": "Low", "color": "#00CC00", "level": 0, "order": 0},
                {"project_id": project_id, "name": "Medium", "color": "#FFCC00", "level": 1, "order": 1},
                {"project_id": project_id, "name": "High", "color": "#FF6600", "level": 2, "order": 2},
                {"project_id": project_id, "name": "Urgent", "color": "#DD0000", "level": 3, "order": 3},
            ],
            default_index=0,
        )
        for priority in priorities:
            self._task_priority_repository.create(priority)

    def create_project(self, schema: ProjectCreate, current_user: User):
        self._ensure_user_in_team(schema.team_id, current_user.id, allow_roles={"owner", "manager"})
        project = self._repository.create(schema)
        self._project_member_repository.create(
            {
                "project_id": project.id,
                "user_id": current_user.id,
                "role": "owner",
            }
        )
        # Seed default catalogs for the new project
        self._seed_project_catalogs(project.id)
        return project

    def get_project_details(self, project_id: str, current_user: User):
        project = self._repository.read_by_id(project_id, eager=True)
        if not project or project.is_deleted:
            raise NotFoundError(detail="Project not found.")

        self._ensure_user_in_team(project.team_id, current_user.id)
        return project

    def update_project(self, project_id: str, schema: ProjectUpdate, current_user: User):
        project = self.get_project_details(project_id, current_user)
        self._ensure_user_in_team(project.team_id, current_user.id, allow_roles={"owner", "manager"})
        return self._repository.update(project_id, schema)

    def delete_project(self, project_id: str, current_user: User):
        project = self.get_project_details(project_id, current_user)
        self._ensure_user_in_team(project.team_id, current_user.id, allow_roles={"owner", "manager"})
        return self._repository.update_attr(project_id, "is_deleted", True)

    def get_my_projects(self, user_id: str):
        return self._repository.get_my_projects(user_id)

    def get_projects(self, find_query: ProjectFind, current_user: User):
        if find_query.team_id__eq:
            self._ensure_user_in_team(find_query.team_id__eq, current_user.id)
        return self._repository.read_by_options(find_query)
