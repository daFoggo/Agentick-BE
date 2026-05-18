from app.core.exceptions import AuthError, NotFoundError
from app.model.user import User
from app.repository.project_repository import ProjectRepository
from app.repository.project_member_repository import ProjectMemberRepository
from app.repository.team_member_repository import TeamMemberRepository
from app.repository.team_repository import TeamRepository
from app.repository.task_status_repository import TaskStatusRepository
from app.repository.task_type_repository import TaskTypeRepository
from app.repository.task_priority_repository import TaskPriorityRepository
from app.repository.unit_of_work import UnitOfWork
from app.schema.project_schema import ProjectCreate, ProjectFind, ProjectUpdate
from app.schema.project_member_schema import ProjectMemberFind
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
        task_repository=None,
    ) -> None:
        super().__init__(repository=project_repository)
        self._team_repository = team_repository
        self._team_member_repository = team_member_repository
        self._project_member_repository = project_member_repository
        self._task_status_repository = task_status_repository
        self._task_type_repository = task_type_repository
        self._task_priority_repository = task_priority_repository
        self._task_repository = task_repository

    def _ensure_user_in_team(
        self, team_id: str, user_id: str, allow_roles: set[str] | None = None
    ):
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

    def _seed_project_catalogs_via_uow(self, uow: UnitOfWork, project_id: str):
        """Seed default TaskStatus, TaskType, and TaskPriority for a new project via UnitOfWork."""

        def _mark_single_default(
            items: list[dict],
            default_index: int = 0,
            completed_index: int | None = None,
        ) -> list[dict]:
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
                {
                    "project_id": project_id,
                    "name": "Backlog",
                    "color": "#8da4c0",
                    "order": 0,
                    "is_completed": False,
                },
                {
                    "project_id": project_id,
                    "name": "To Do",
                    "color": "#6c8ebf",
                    "order": 1,
                    "is_completed": False,
                },
                {
                    "project_id": project_id,
                    "name": "In Progress",
                    "color": "#3BA6F1",
                    "order": 2,
                    "is_completed": False,
                },
                {
                    "project_id": project_id,
                    "name": "In Review",
                    "color": "#fdba74",
                    "order": 3,
                    "is_completed": False,
                },
                {
                    "project_id": project_id,
                    "name": "Blocked",
                    "color": "#fb7185",
                    "order": 4,
                    "is_completed": False,
                },
                {
                    "project_id": project_id,
                    "name": "Done",
                    "color": "#97D6AE",
                    "order": 5,
                    "is_completed": False,
                },
            ],
            default_index=1,
            completed_index=5,
        )
        for status in statuses:
            uow.task_statuses.create(status, auto_commit=False)

        # Default Task Types
        types = _mark_single_default(
            [
                {
                    "project_id": project_id,
                    "name": "Task",
                    "color": "#6c8ebf",
                    "icon": "list-checks",
                    "order": 0,
                },
                {
                    "project_id": project_id,
                    "name": "Feature",
                    "color": "#3BA6F1",
                    "icon": "sparkles",
                    "order": 1,
                },
                {
                    "project_id": project_id,
                    "name": "Bug",
                    "color": "#fb7185",
                    "icon": "bug",
                    "order": 2,
                },
                {
                    "project_id": project_id,
                    "name": "Epic",
                    "color": "#a78bfa",
                    "icon": "layers-3",
                    "order": 3,
                },
                {
                    "project_id": project_id,
                    "name": "Sub-task",
                    "color": "#97D6AE",
                    "icon": "subtitles",
                    "order": 4,
                },
            ],
            default_index=0,
        )
        for task_type in types:
            uow.task_types.create(task_type, auto_commit=False)

        # Default Task Priorities
        priorities = _mark_single_default(
            [
                {
                    "project_id": project_id,
                    "name": "Lowest",
                    "color": "#8da4c0",
                    "level": 0,
                    "order": 0,
                },
                {
                    "project_id": project_id,
                    "name": "Low",
                    "color": "#97D6AE",
                    "level": 1,
                    "order": 1,
                },
                {
                    "project_id": project_id,
                    "name": "Medium",
                    "color": "#3BA6F1",
                    "level": 2,
                    "order": 2,
                },
                {
                    "project_id": project_id,
                    "name": "High",
                    "color": "#fdba74",
                    "level": 3,
                    "order": 3,
                },
                {
                    "project_id": project_id,
                    "name": "Highest",
                    "color": "#fb7185",
                    "level": 4,
                    "order": 4,
                },
            ],
            default_index=2,
        )
        for priority in priorities:
            uow.task_priorities.create(priority, auto_commit=False)

    def create_project(self, schema: ProjectCreate, current_user: User):
        self._ensure_user_in_team(
            schema.team_id, current_user.id, allow_roles={"owner", "manager"}
        )

        # Use Unit of Work for atomic transaction across multiple tables
        with UnitOfWork(self._repository.session_factory) as uow:
            project = uow.projects.create(schema, auto_commit=False)
            # Re-inject dynamically assigned ID so we can reference it
            # even before commit (since flush generates it)
            uow.project_members.create(
                {
                    "project_id": project.id,
                    "user_id": current_user.id,
                    "role": "owner",
                },
                auto_commit=False,
            )
            # Seed default catalogs for the new project
            self._seed_project_catalogs_via_uow(uow, project.id)

            # Unit of Work automatically commits when exiting the context manager
            # if no exception occurred.

            # Need to get the actual project model back in local scope for return
            return project

    def get_project_details(self, project_id: str, current_user: User):
        project = self._repository.read_by_id(project_id, eager=True)
        if not project or project.is_deleted:
            raise NotFoundError(detail="Project not found.")

        # Check if user is a member of this PROJECT
        member = self._project_member_repository.read_by_options(
            ProjectMemberFind(project_id__eq=project_id, user_id__eq=current_user.id)
        )
        if not member.get("founds"):
            raise AuthError(detail="You are not a member of this project.")

        if self._task_repository:
            stats = self._task_repository.get_projects_stats([project_id])
            project.stats = stats.get(project_id)

        return project

    def update_project(
        self, project_id: str, schema: ProjectUpdate, current_user: User
    ):
        self.get_project_details(project_id, current_user)
        member = self._project_member_repository.read_by_options(
            ProjectMemberFind(project_id__eq=project_id, user_id__eq=current_user.id)
        )
        role = member["founds"][0].role if member.get("founds") else None
        if role not in {"owner", "manager"}:
            raise AuthError(detail="Insufficient privileges for this action.")
        return self._repository.update(project_id, schema)

    def delete_project(self, project_id: str, current_user: User):
        self.get_project_details(project_id, current_user)
        member = self._project_member_repository.read_by_options(
            ProjectMemberFind(project_id__eq=project_id, user_id__eq=current_user.id)
        )
        role = member["founds"][0].role if member.get("founds") else None
        if role not in {"owner", "manager"}:
            raise AuthError(detail="Insufficient privileges for this action.")

        # Soft-delete all tasks of this project and delete their calendar events
        self._repository.cleanup_project_resources_on_delete(project_id)

        return self._repository.update_attr(project_id, "is_deleted", True)

    def get_my_projects(self, user_id: str, team_id: str | None = None):
        projects = self._repository.get_my_projects(user_id, team_id=team_id)
        if self._task_repository and projects:
            project_ids = [p.id for p in projects]
            stats_map = self._task_repository.get_projects_stats(project_ids)
            for p in projects:
                p.stats = stats_map.get(p.id)
        return projects

    def get_projects(self, find_query: ProjectFind, current_user: User):
        # Always filter projects by user membership
        # This overrides the repository's default search to ensure privacy
        projects = self._repository.get_my_projects(
            current_user.id, team_id=find_query.team_id__eq
        )

        if self._task_repository and projects:
            project_ids = [p.id for p in projects]
            stats_map = self._task_repository.get_projects_stats(project_ids)
            for p in projects:
                p.stats = stats_map.get(p.id)

        return {
            "founds": projects,
            "search_options": {
                "total_count": len(projects),
                "page": find_query.page or 1,
                "page_size": find_query.page_size or len(projects),
                "ordering": find_query.ordering,
            },
        }
