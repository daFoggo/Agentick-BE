import logging
import threading
from fastapi import HTTPException, status
from app.model.user import User
from app.model.invitation import Invitation, InvitationStatus
from app.repository.invitation_repository import InvitationRepository
from app.repository.team_member_repository import TeamMemberRepository
from app.repository.project_member_repository import ProjectMemberRepository
from app.model.team_member import TeamMember
from app.model.project_member import ProjectMember
from app.schema.team_member_schema import TeamMemberFind
from app.schema.project_member_schema import ProjectMemberFind
from app.utils.email import send_invitation_email
from app.core.config import configs

logger = logging.getLogger(__name__)

class InvitationService:
    def __init__(
        self,
        invitation_repository: InvitationRepository,
        team_member_repository: TeamMemberRepository,
        project_member_repository: ProjectMemberRepository,
    ):
        self.invitation_repository = invitation_repository
        self.team_member_repository = team_member_repository
        self.project_member_repository = project_member_repository

    def get_my_pending_invitations(self, current_user: User) -> list[Invitation]:
        return self.invitation_repository.get_pending_by_email(current_user.email, eager=True)

    def get_invitation_by_id(self, invitation_id: str) -> Invitation:
        invitation = self.invitation_repository.read_by_id(invitation_id, eager=True)
        if not invitation:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invitation not found")
        return invitation

    def accept_invitation(self, invitation_id: str, current_user: User) -> Invitation:
        invitation = self.invitation_repository.read_by_id(invitation_id, eager=True)
        if not invitation:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invitation not found")

        if invitation.status != InvitationStatus.PENDING:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invitation is no longer valid")

        if invitation.email.strip().lower() != current_user.email.strip().lower():
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not allowed to accept this invitation")

        # Process the acceptance
        if invitation.team_id:
            # Add to team
            existing = self.team_member_repository.read_by_options(
                TeamMemberFind(team_id__eq=invitation.team_id, user_id__eq=current_user.id)
            )
            if not existing.get("founds"):
                member_data = {
                    "team_id": invitation.team_id,
                    "user_id": current_user.id,
                    "role": invitation.role
                }
                self.team_member_repository.create(member_data)
        if invitation.project_id:
            # Add to project
            existing_project_member = self.project_member_repository.read_by_options(
                ProjectMemberFind(project_id__eq=invitation.project_id, user_id__eq=current_user.id)
            )
            if not existing_project_member.get("founds"):
                member_data = {
                    "project_id": invitation.project_id,
                    "user_id": current_user.id,
                    "role": invitation.role
                }
                self.project_member_repository.create(member_data)
            
            # ALSO add to team so they can access the team dashboard context
            # We need to find the team_id from the project
            # (Note: Invitation record for projects might not have team_id set if not passed during creation)
            # But the invitation record WE create for projects should ideally have team_id too if possible.
            # Let's check invitation.team_id first, if not, we'd need a project repository (which we don't have here)
            # Actually, let's just make sure team_id is passed during project invitation creation.
            if invitation.team_id:
                existing_team_member = self.team_member_repository.read_by_options(
                    TeamMemberFind(team_id__eq=invitation.team_id, user_id__eq=current_user.id)
                )
                if not existing_team_member.get("founds"):
                    self.team_member_repository.create({
                        "team_id": invitation.team_id,
                        "user_id": current_user.id,
                        "role": "member" # Default to member in team if invited to specific project
                    })

        # Update status
        updated_invitation = self.invitation_repository.update(invitation_id, {"status": InvitationStatus.ACCEPTED}, eager=True)
        return updated_invitation

    def decline_invitation(self, invitation_id: str, current_user: User) -> Invitation:
        invitation = self.invitation_repository.read_by_id(invitation_id, eager=True)
        if not invitation:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invitation not found")

        if invitation.status != InvitationStatus.PENDING:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invitation is no longer valid")

        if invitation.email.strip().lower() != current_user.email.strip().lower():
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not allowed to decline this invitation")

        updated_invitation = self.invitation_repository.update(invitation_id, {"status": InvitationStatus.DECLINED}, eager=True)
        return updated_invitation

    def create_and_send_invitation(self, email: str, inviter: User, role: str, team_id: str = None, project_id: str = None, target_name: str = None) -> Invitation:
        # Create invitation record
        invitation_data = {
            "email": email.strip(),
            "inviter_id": inviter.id,
            "team_id": team_id,
            "project_id": project_id,
            "role": role,
            "status": InvitationStatus.PENDING
        }
        created_invitation = self.invitation_repository.create(invitation_data)

        # Send email in background thread
        target_type = "project" if project_id else "team"
        invite_link = f"{configs.FRONTEND_URL}/invite/accept?id={created_invitation.id}"

        threading.Thread(
            target=send_invitation_email,
            args=(email, inviter.name, target_name, invite_link, target_type)
        ).start()

        return created_invitation
