from contextlib import nullcontext
from typing import Any, List
from fastapi import APIRouter, Depends

from app.core.dependencies import get_db, get_current_active_user
from app.model.user import User
from app.repository.work_schedule_repository import WorkScheduleRepository
from app.repository.team_member_repository import TeamMemberRepository
from app.schema.base_schema import ResponseSchema
from app.schema.schedule_schema import (
    WorkScheduleCreate,
    WorkScheduleRead,
)
from app.services.schedule_service import ScheduleService

router = APIRouter(prefix="/schedules", tags=["schedules"])


def get_schedule_service(db=Depends(get_db)) -> ScheduleService:
    work_repo = WorkScheduleRepository(lambda: nullcontext(db))
    return ScheduleService(work_schedule_repository=work_repo)


@router.get("/me", response_model=ResponseSchema[List[WorkScheduleRead]])
def get_my_patterns(
    current_user: User = Depends(get_current_active_user),
    service: ScheduleService = Depends(get_schedule_service),
):
    """
    Get current user's 7-day recurring pattern config.
    """
    result = service.get_user_patterns(current_user.id)
    return ResponseSchema(data=result)


@router.post("/me", response_model=ResponseSchema[WorkScheduleRead])
def upsert_my_pattern(
    schema: WorkScheduleCreate,
    current_user: User = Depends(get_current_active_user),
    service: ScheduleService = Depends(get_schedule_service),
):
    """
    Create or update a single day pattern for the current user.
    """
    schema.user_id = current_user.id
    result = service.upsert_pattern(schema)
    return ResponseSchema(data=result)


@router.get("/teams/{team_id}", response_model=ResponseSchema[List[Any]])
def get_team_patterns(
    team_id: str,
    service: ScheduleService = Depends(get_schedule_service),
    db=Depends(get_db)
):
    """
    Get 7-day recurring patterns for all members of a team.
    """
    team_member_repo = TeamMemberRepository(lambda: nullcontext(db))
    members = team_member_repo.read_by_options({"team_id__eq": team_id})["founds"]
    
    results = []
    for m in members:
        patterns = service.get_user_patterns(m.user_id)
        results.append({
            "user_id": m.user_id,
            "patterns": patterns
        })
    return ResponseSchema(data=results)
