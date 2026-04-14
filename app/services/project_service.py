from app.core.exceptions import AuthError, NotFoundError
from app.model.user import User
from app.repository.project_repository import ProjectRepository
from app.repository.project_member_repository import ProjectMemberRepository
from app.repository.team_member_repository import TeamMemberRepository
from app.repository.team_repository import TeamRepository
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
    ) -> None:
        super().__init__(repository=project_repository)
        self._team_repository = team_repository
        self._team_member_repository = team_member_repository
        self._project_member_repository = project_member_repository

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
