from app.repository.team_member_repository import TeamMemberRepository
from app.repository.team_repository import TeamRepository
from app.repository.project_member_repository import ProjectMemberRepository
from app.schema.team_member_schema import TeamMemberCreate, TeamMemberUpdate, TeamMemberFind
from app.services.base_service import BaseService
from app.model.user import User
from app.core.exceptions import AuthError, NotFoundError, DuplicatedError


class TeamMemberService(BaseService):
    def __init__(
        self,
        team_member_repository: TeamMemberRepository,
        team_repository: TeamRepository,
        project_member_repository: ProjectMemberRepository,
    ) -> None:
        super().__init__(repository=team_member_repository)
        self._team_repository = team_repository
        self._project_member_repository = project_member_repository

    def add_member(self, team_id: str, schema: TeamMemberCreate, current_user: User):
        # 1. Check team exists and not deleted
        team = self._team_repository.read_by_id(team_id)
        if not team or team.is_deleted:
            raise NotFoundError(detail="Team not found.")
        
        # 2. Check permission (OWNER or MANAGER)
        # We need to find the current user's role in the team
        current_member = self._repository.read_by_options(TeamMemberFind(team_id__eq=team_id, user_id__eq=current_user.id))
        if not current_member.get("founds") or current_member["founds"][0].role not in ["owner", "manager"]:
            raise AuthError(detail="Insufficient privileges to add members.")

        # 3. Check if user already a member
        existing_member = self._repository.read_by_options(TeamMemberFind(team_id__eq=team_id, user_id__eq=schema.user_id))
        if existing_member.get("founds"):
            raise DuplicatedError(detail="User is already a member of this team.")

        # 4. Add member
        member_data = schema.model_dump()
        member_data["team_id"] = team_id
        return self._repository.create(member_data)

    def get_members(self, find_query: TeamMemberFind):
        if find_query.q:
            return self._repository.search_members(
                team_id=find_query.team_id__eq,
                q=find_query.q,
                page=find_query.page,
                page_size=find_query.page_size
            )
        return self._repository.read_by_options(find_query)

    def get_member_project_count(self, team_id: str, user_id: str) -> int:
        return self._project_member_repository.count_projects_in_team(team_id, user_id)

    def update_member_role(self, team_id: str, user_id: str, schema: TeamMemberUpdate, current_user: User):
        # Check permission
        current_member = self._repository.read_by_options(TeamMemberFind(team_id__eq=team_id, user_id__eq=current_user.id))
        if not current_member.get("founds") or current_member["founds"][0].role not in ["owner", "manager"]:
            raise AuthError(detail="Insufficient privileges to update roles.")
        
        # Find member to update
        target_member = self._repository.read_by_options(TeamMemberFind(team_id__eq=team_id, user_id__eq=user_id))
        if not target_member.get("founds"):
            raise NotFoundError(detail="Member not found.")
        
        return self._repository.update(target_member["founds"][0].id, schema)

    def remove_member(self, team_id: str, user_id: str, current_user: User):
        # Check permission
        current_member = self._repository.read_by_options(TeamMemberFind(team_id__eq=team_id, user_id__eq=current_user.id))
        if not current_member.get("founds") or current_member["founds"][0].role not in ["owner", "manager"]:
            # User can remove themselves
            if current_user.id != user_id:
                raise AuthError(detail="Insufficient privileges to remove members.")
        
        # Find member to remove
        target_member = self._repository.read_by_options(TeamMemberFind(team_id__eq=team_id, user_id__eq=user_id))
        if not target_member.get("founds"):
            raise NotFoundError(detail="Member not found.")
        
        # Prevent removing the only owner
        if target_member["founds"][0].role == "owner":
            all_owners = self._repository.read_by_options(TeamMemberFind(team_id__eq=team_id, role__eq="owner"))
            if len(all_owners.get("founds", [])) <= 1:
                raise AuthError(detail="Cannot remove the only owner of the team.")

        # Cascading removal from all projects in the team
        self._project_member_repository.remove_from_all_team_projects(team_id, user_id)

        # Remove from the team itself
        return self._repository.delete_by_id(target_member["founds"][0].id)
