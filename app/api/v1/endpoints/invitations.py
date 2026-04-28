from contextlib import nullcontext
from fastapi import APIRouter, Depends
from typing import List

from app.core.dependencies import get_db, get_current_active_user
from app.model.user import User
from app.repository.invitation_repository import InvitationRepository
from app.repository.team_member_repository import TeamMemberRepository
from app.repository.project_member_repository import ProjectMemberRepository
from app.schema.base_schema import ResponseSchema
from app.schema.invitation_schema import InvitationResponse
from app.services.invitation_service import InvitationService

router = APIRouter(prefix="/invitations", tags=["invitations"])

def get_invitation_service(db=Depends(get_db)) -> InvitationService:
    invitation_repository = InvitationRepository(lambda: nullcontext(db))
    team_member_repository = TeamMemberRepository(lambda: nullcontext(db))
    project_member_repository = ProjectMemberRepository(lambda: nullcontext(db))
    return InvitationService(
        invitation_repository=invitation_repository,
        team_member_repository=team_member_repository,
        project_member_repository=project_member_repository,
    )

@router.get("/me", response_model=ResponseSchema[List[InvitationResponse]])
def get_my_invitations(
    current_user: User = Depends(get_current_active_user),
    service: InvitationService = Depends(get_invitation_service)
):
    invitations = service.get_my_pending_invitations(current_user)
    return ResponseSchema(data=invitations, message="Pending invitations fetched successfully")

@router.get("/{invitation_id}", response_model=ResponseSchema[InvitationResponse])
def get_invitation(
    invitation_id: str,
    service: InvitationService = Depends(get_invitation_service)
):
    invitation = service.get_invitation_by_id(invitation_id)
    return ResponseSchema(data=invitation, message="Invitation fetched successfully")

@router.post("/{invitation_id}/accept", response_model=ResponseSchema[InvitationResponse])
def accept_invitation(
    invitation_id: str,
    current_user: User = Depends(get_current_active_user),
    service: InvitationService = Depends(get_invitation_service)
):
    invitation = service.accept_invitation(invitation_id, current_user)
    return ResponseSchema(data=invitation, message="Invitation accepted successfully")

@router.post("/{invitation_id}/decline", response_model=ResponseSchema[InvitationResponse])
def decline_invitation(
    invitation_id: str,
    current_user: User = Depends(get_current_active_user),
    service: InvitationService = Depends(get_invitation_service)
):
    invitation = service.decline_invitation(invitation_id, current_user)
    return ResponseSchema(data=invitation, message="Invitation declined successfully")
