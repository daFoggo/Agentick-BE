from app.model.user import User
from app.repository.user_repository import UserRepository
from app.repository.team_member_repository import TeamMemberRepository
from app.schema.auth_schema import UserInfo
from app.schema.user_schema import UserSearchResult
from app.schema.team_member_schema import TeamMemberFind


class UserService:
    def __init__(
        self,
        user_repository: UserRepository,
        team_member_repository: TeamMemberRepository | None = None,
    ) -> None:
        self._user_repository = user_repository
        self._team_member_repository = team_member_repository

    @staticmethod
    def to_user_info(user: User) -> UserInfo:
        return UserInfo.model_validate(user)

    def get_me(self, user: User) -> UserInfo:
        return self.to_user_info(user)

    def search_users(
        self,
        query: str,
        limit: int = 10,
        exclude_user_ids: list[str] | None = None,
        team_id: str | None = None,
    ) -> list[UserSearchResult]:
        """Search users by email or name, optionally excluding existing team members."""
        ids_to_exclude = list(exclude_user_ids) if exclude_user_ids else []

        # If team_id is provided, exclude users already in that team
        if team_id and self._team_member_repository:
            result = self._team_member_repository.read_by_options(
                TeamMemberFind(team_id__eq=team_id)
            )
            existing_members = result.get("founds", [])
            ids_to_exclude.extend(m.user_id for m in existing_members)

        users = self._user_repository.search_users(
            query=query,
            limit=limit,
            exclude_user_ids=ids_to_exclude if ids_to_exclude else None,
        )
        return [UserSearchResult.model_validate(u) for u in users]

