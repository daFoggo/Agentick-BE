from app.repository.team_repository import TeamRepository
from app.repository.team_member_repository import TeamMemberRepository
from app.schema.team_schema import TeamCreate, TeamUpdate
from app.schema.team_member_schema import TeamMemberFind
from app.services.base_service import BaseService
from app.model.user import User
from app.core.exceptions import AuthError, NotFoundError


class TeamService(BaseService):
    def __init__(
        self,
        team_repository: TeamRepository,
        team_member_repository: TeamMemberRepository,
        task_repository=None,
    ) -> None:
        super().__init__(repository=team_repository)
        self._team_member_repository = team_member_repository
        self._task_repository = task_repository

    def create_team(self, schema: TeamCreate, owner: User, auto_commit: bool = True):
        # 1. Create Team
        team_data = schema.model_dump()
        team_data["owner_id"] = owner.id
        team = self._repository.create(team_data, auto_commit=auto_commit)

        # 2. Add owner as member with 'owner' role
        member_data = {"team_id": team.id, "user_id": owner.id, "role": "owner"}
        self._team_member_repository.create(member_data, auto_commit=auto_commit)

        return team

    def get_team_details(self, team_id: str):
        team = self._repository.read_by_id(team_id)
        if not team or team.is_deleted:
            raise NotFoundError(detail="Team not found.")

        if self._task_repository:
            stats = self._task_repository.get_teams_stats([team_id])
            team.stats = stats.get(team_id)

        return team

    def _ensure_team_role(self, team_id: str, user_id: str, allowed_roles: set[str]):
        team = self.get_team_details(team_id)
        current_member = self._team_member_repository.read_by_options(
            TeamMemberFind(team_id__eq=team_id, user_id__eq=user_id)
        )
        if not current_member.get("founds"):
            raise AuthError(detail="You are not a member of this team.")

        role = current_member["founds"][0].role
        if role not in allowed_roles:
            raise AuthError(detail="Insufficient privileges for this team.")

        return team

    def get_team_details_for_user(self, team_id: str, current_user: User):
        return self._ensure_team_role(
            team_id, current_user.id, {"owner", "manager", "member", "viewer"}
        )

    def update_team(self, team_id: str, schema: TeamUpdate, current_user: User):
        self._ensure_team_role(team_id, current_user.id, {"owner"})

        return self._repository.update(team_id, schema)

    def delete_team(self, team_id: str, current_user: User):
        self._ensure_team_role(team_id, current_user.id, {"owner"})

        # Soft delete
        return self._repository.update_attr(team_id, "is_deleted", True)

    def get_my_teams(self, user_id: str):
        teams = self._repository.get_my_teams(user_id)
        if self._task_repository and teams:
            team_ids = [t.id for t in teams]
            stats_map = self._task_repository.get_teams_stats(team_ids)
            for t in teams:
                t.stats = stats_map.get(t.id)
        return teams
