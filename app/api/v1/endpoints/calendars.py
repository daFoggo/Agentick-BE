from contextlib import nullcontext
from fastapi import APIRouter, Depends

from app.core.dependencies import get_db, get_current_active_user
from app.model.user import User
from app.repository.calendar_repository import CalendarRepository
from app.repository.team_member_repository import TeamMemberRepository
from app.schema.base_schema import ResponseSchema
from app.schema.calendar_schema import CalendarRead

router = APIRouter(prefix="/calendars", tags=["calendars"])


@router.get("", response_model=ResponseSchema[list[CalendarRead]])
def get_my_calendars(
    current_user: User = Depends(get_current_active_user),
    db=Depends(get_db)
):
    """
    Get all calendars accessible by the current user.
    Includes personal calendar and team calendars.
    """
    calendar_repo = CalendarRepository(lambda: nullcontext(db))
    team_member_repo = TeamMemberRepository(lambda: nullcontext(db))
    
    # 1. Get teams user is in
    team_members = team_member_repo.read_by_options({"user_id__eq": current_user.id})["founds"]
    team_ids = [tm.team_id for tm in team_members]
    
    # 2. Get personal calendar
    personal_calendars = calendar_repo.read_by_options({
        "owner_id__eq": current_user.id,
        "type__eq": "personal"
    })["founds"]
    
    # 3. Get team calendars
    team_calendars = []
    if team_ids:
        # Simple loop for now
        for t_id in team_ids:
            tc = calendar_repo.read_by_options({
                "owner_id__eq": t_id,
                "type__eq": "team"
            })["founds"]
            team_calendars.extend(tc)
            
    return ResponseSchema(data=personal_calendars + team_calendars)
