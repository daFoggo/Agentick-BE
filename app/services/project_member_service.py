from app.core.exceptions import AuthError, DuplicatedError, NotFoundError
from app.core.security import create_invite_token, decode_jwt
from app.model.user import User
from app.repository.project_member_repository import ProjectMemberRepository
from app.repository.project_repository import ProjectRepository
from app.repository.team_member_repository import TeamMemberRepository
from app.schema.project_member_schema import (
    ProjectMemberCreate,
    ProjectMemberFind,
    ProjectMemberUpdate,
)
from app.schema.team_member_schema import TeamMemberFind
from app.services.base_service import BaseService


class ProjectMemberService(BaseService):
    def __init__(
        self,
        project_member_repository: ProjectMemberRepository,
        project_repository: ProjectRepository,
        team_member_repository: TeamMemberRepository,
    ) -> None:
        super().__init__(repository=project_member_repository)
        self._project_repository = project_repository
        self._team_member_repository = team_member_repository

    def _get_project_or_raise(self, project_id: str):
        project = self._project_repository.read_by_id(project_id)
        if not project or project.is_deleted:
            raise NotFoundError(detail="Project not found.")
        return project

    def _ensure_team_manager(self, team_id: str, user_id: str):
        current_member = self._team_member_repository.read_by_options(
            TeamMemberFind(team_id__eq=team_id, user_id__eq=user_id)
        )
        if not current_member.get("founds") or current_member["founds"][0].role not in [
            "owner",
            "manager",
        ]:
            raise AuthError(detail="Insufficient privileges to manage project members.")

    def add_member(
        self, project_id: str, schema: ProjectMemberCreate, current_user: User
    ):
        project = self._get_project_or_raise(project_id)
        self._ensure_team_manager(project.team_id, current_user.id)

        target_team_member = self._team_member_repository.read_by_options(
            TeamMemberFind(team_id__eq=project.team_id, user_id__eq=schema.user_id)
        )
        if not target_team_member.get("founds"):
            # If user not in team, add them automatically with role 'member'
            self._team_member_repository.create(
                {
                    "team_id": project.team_id,
                    "user_id": schema.user_id,
                    "role": "member",
                }
            )

        existing_member = self._repository.read_by_options(
            ProjectMemberFind(project_id__eq=project_id, user_id__eq=schema.user_id)
        )
        if existing_member.get("founds"):
            raise DuplicatedError(detail="User is already a member of this project.")

        member_data = schema.model_dump()
        member_data["project_id"] = project_id
        return self._repository.create(member_data)

    def get_members(self, project_id: str, current_user: User):
        project = self._get_project_or_raise(project_id)

        team_member = self._team_member_repository.read_by_options(
            TeamMemberFind(team_id__eq=project.team_id, user_id__eq=current_user.id)
        )
        if not team_member.get("founds"):
            raise AuthError(detail="You are not a member of this team.")

        return self._repository.read_by_options(
            ProjectMemberFind(project_id__eq=project_id), eager=True
        )

    def generate_invite_token(
        self, project_id: str, email: str, role: str, current_user: User
    ) -> str:
        project = self._get_project_or_raise(project_id)
        self._ensure_team_manager(project.team_id, current_user.id)

        subject = {
            "project_id": project_id,
            "email": email,
            "role": role,
            "invite_type": "project",
        }
        token, _ = create_invite_token(subject)
        return token

    def accept_invite_token(self, token: str, current_user: User):
        decoded = decode_jwt(token)
        if (
            not decoded
            or decoded.get("type") != "invite"
            or decoded.get("invite_type") != "project"
        ):
            raise AuthError(detail="Invalid or expired invitation token.")

        if decoded.get("email") != current_user.email:
            raise AuthError(
                detail="This invitation was sent to a different email address."
            )

        project_id = decoded.get("project_id")
        role = decoded.get("role")

        project = self._get_project_or_raise(project_id)

        # Ensure user is in the team first before joining project
        target_team_member = self._team_member_repository.read_by_options(
            TeamMemberFind(team_id__eq=project.team_id, user_id__eq=current_user.id)
        )
        if not target_team_member.get("founds"):
            # Auto-join team as member
            self._team_member_repository.create(
                {
                    "team_id": project.team_id,
                    "user_id": current_user.id,
                    "role": "member",
                }
            )

        existing_member = self._repository.read_by_options(
            ProjectMemberFind(project_id__eq=project_id, user_id__eq=current_user.id)
        )
        if existing_member.get("founds"):
            raise DuplicatedError(detail="You are already a member of this project.")

        member_data = {
            "project_id": project_id,
            "user_id": current_user.id,
            "role": role,
        }
        return self._repository.create(member_data)

    def update_member_role(
        self,
        project_id: str,
        user_id: str,
        schema: ProjectMemberUpdate,
        current_user: User,
    ):
        project = self._get_project_or_raise(project_id)
        self._ensure_team_manager(project.team_id, current_user.id)

        target_member = self._repository.read_by_options(
            ProjectMemberFind(project_id__eq=project_id, user_id__eq=user_id)
        )
        if not target_member.get("founds"):
            raise NotFoundError(detail="Member not found.")

        return self._repository.update(target_member["founds"][0].id, schema)

    def remove_member(self, project_id: str, user_id: str, current_user: User):
        project = self._get_project_or_raise(project_id)
        if user_id != current_user.id:
            self._ensure_team_manager(project.team_id, current_user.id)

        target_member = self._repository.read_by_options(
            ProjectMemberFind(project_id__eq=project_id, user_id__eq=user_id)
        )
        if not target_member.get("founds"):
            raise NotFoundError(detail="Member not found.")

        if target_member["founds"][0].role == "owner":
            all_owners = self._repository.read_by_options(
                ProjectMemberFind(project_id__eq=project_id, role__eq="owner")
            )
            if len(all_owners.get("founds", [])) <= 1:
                raise AuthError(detail="Cannot remove the only owner of the project.")

        return self._repository.delete_by_id(target_member["founds"][0].id)

    def check_permission(
        self, project_id: str, user_id: str, required_role: str = "manager"
    ):
        """Checks if a user has sufficient role in the project's team."""
        project = self._get_project_or_raise(project_id)
        # For now, project management permission is tied to team role
        return self._ensure_team_manager(project.team_id, user_id)

    def is_user_member(self, project_id: str, user_id: str) -> bool:
        """Checks if a user is a member of the project."""
        member = self._repository.read_by_options(
            ProjectMemberFind(project_id__eq=project_id, user_id__eq=user_id)
        )
        return bool(member.get("founds"))

    def get_project_member_workload(self, project_id: str, period: str):
        from datetime import datetime, timedelta, timezone
        from app.schema.task_schema import (
            MemberWorkload,
            ProjectWorkloadResponse,
            WorkloadDataPoint,
        )

        now = datetime.now(timezone.utc)
        delta = timedelta(days=7) if period == "weekly" else timedelta(days=30)
        date_from = now - delta
        date_to = now

        member_raw_data = self._repository.get_member_workload_raw(
            project_id, date_from, date_to
        )

        result_members: list[MemberWorkload] = []

        for member, rows in member_raw_data:
            user = member.user
            if not user:
                continue

            count_by_day: dict[str, int] = {
                str(row.day): row.task_count for row in rows
            }

            # Fill range fully
            vn_offset = timedelta(hours=7)
            local_start = (date_from + vn_offset).date()
            local_end = (date_to + vn_offset).date() + timedelta(days=1)

            series: list[WorkloadDataPoint] = []
            current_day = local_start
            while current_day < local_end:
                day_str = current_day.isoformat()
                series.append(
                    WorkloadDataPoint(
                        date=day_str, task_count=count_by_day.get(day_str, 0)
                    )
                )
                current_day += timedelta(days=1)

            result_members.append(
                MemberWorkload(
                    user_id=user.id,
                    name=user.name,
                    avatar_url=user.avatar_url,
                    series=series,
                )
            )

        return ProjectWorkloadResponse(
            members=result_members,
            period=period,
            date_from=date_from.date().isoformat(),
            date_to=date_to.date().isoformat(),
        )
