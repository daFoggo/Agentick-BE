from contextlib import nullcontext
from typing import List
from fastapi import APIRouter, Depends

from app.core.dependencies import get_db, get_current_active_user
from app.model.user import User
from app.repository.team_repository import TeamRepository
from app.repository.team_member_repository import TeamMemberRepository
from app.schema.base_schema import ResponseSchema, FindResult
from app.schema.team_schema import TeamCreate, TeamRead, TeamUpdate, TeamFind
from app.schema.team_member_schema import TeamMemberCreate, TeamMemberRead, TeamMemberUpdate
from app.services.team_service import TeamService
from app.services.team_member_service import TeamMemberService

router = APIRouter(prefix="/teams", tags=["teams"])


def get_team_service(db=Depends(get_db)) -> TeamService:
    team_repository = TeamRepository(lambda: nullcontext(db))
    team_member_repository = TeamMemberRepository(lambda: nullcontext(db))
    return TeamService(team_repository=team_repository, team_member_repository=team_member_repository)


def get_team_member_service(db=Depends(get_db)) -> TeamMemberService:
    team_member_repository = TeamMemberRepository(lambda: nullcontext(db))
    team_repository = TeamRepository(lambda: nullcontext(db))
    return TeamMemberService(team_member_repository=team_member_repository, team_repository=team_repository)


# --- Team Endpoints ---

@router.post("", response_model=ResponseSchema[TeamRead])
def create_team(
    schema: TeamCreate,
    current_user: User = Depends(get_current_active_user),
    service: TeamService = Depends(get_team_service)
):
    result = service.create_team(schema, current_user)
    return ResponseSchema(data=result, message="Team created successfully")


@router.get("", response_model=ResponseSchema[FindResult[TeamRead]])
def get_teams(
    find_query: TeamFind = Depends(),
    service: TeamService = Depends(get_team_service)
):
    result = service.get_list(find_query)
    return ResponseSchema(data=result)


@router.get("/{team_id}", response_model=ResponseSchema[TeamRead])
def get_team(
    team_id: str,
    service: TeamService = Depends(get_team_service)
):
    result = service.get_team_details(team_id)
    return ResponseSchema(data=result)


@router.patch("/{team_id}", response_model=ResponseSchema[TeamRead])
def update_team(
    team_id: str,
    schema: TeamUpdate,
    current_user: User = Depends(get_current_active_user),
    service: TeamService = Depends(get_team_service)
):
    result = service.update_team(team_id, schema, current_user)
    return ResponseSchema(data=result, message="Team updated successfully")


@router.delete("/{team_id}", response_model=ResponseSchema[bool])
def delete_team(
    team_id: str,
    current_user: User = Depends(get_current_active_user),
    service: TeamService = Depends(get_team_service)
):
    service.delete_team(team_id, current_user)
    return ResponseSchema(data=True, message="Team deleted successfully")


# --- Team Member Endpoints ---

@router.get("/{team_id}/members", response_model=ResponseSchema[FindResult[TeamMemberRead]])
def get_team_members(
    team_id: str,
    service: TeamMemberService = Depends(get_team_member_service)
):
    result = service.get_members(team_id)
    return ResponseSchema(data=result)


@router.post("/{team_id}/members", response_model=ResponseSchema[TeamMemberRead])
def add_team_member(
    team_id: str,
    schema: TeamMemberCreate,
    current_user: User = Depends(get_current_active_user),
    service: TeamMemberService = Depends(get_team_member_service)
):
    result = service.add_member(team_id, schema, current_user)
    return ResponseSchema(data=result, message="Member added successfully")


@router.patch("/{team_id}/members/{user_id}", response_model=ResponseSchema[TeamMemberRead])
def update_team_member(
    team_id: str,
    user_id: str,
    schema: TeamMemberUpdate,
    current_user: User = Depends(get_current_active_user),
    service: TeamMemberService = Depends(get_team_member_service)
):
    result = service.update_member_role(team_id, user_id, schema, current_user)
    return ResponseSchema(data=result, message="Member role updated successfully")


@router.delete("/{team_id}/members/{user_id}", response_model=ResponseSchema[bool])
def remove_team_member(
    team_id: str,
    user_id: str,
    current_user: User = Depends(get_current_active_user),
    service: TeamMemberService = Depends(get_team_member_service)
):
    service.remove_member(team_id, user_id, current_user)
    return ResponseSchema(data=True, message="Member removed successfully")
