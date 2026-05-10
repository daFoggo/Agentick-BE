from contextlib import nullcontext

from fastapi import APIRouter, Depends

from app.core.dependencies import get_current_active_user, get_db
from app.model.user import User
from app.repository.calendar_repository import CalendarRepository
from app.repository.event_repository import EventRepository
from app.repository.team_member_repository import TeamMemberRepository
from app.schema.base_schema import ResponseSchema
from app.schema.calendar_schema import CalendarRead
from app.services.calendar_service import CalendarService

router = APIRouter(prefix="/calendars", tags=["calendars"])


def get_calendar_service(db=Depends(get_db)) -> CalendarService:
    calendar_repo = CalendarRepository(lambda: nullcontext(db))
    event_repo = EventRepository(lambda: nullcontext(db))
    team_member_repo = TeamMemberRepository(lambda: nullcontext(db))
    return CalendarService(
        calendar_repository=calendar_repo,
        event_repository=event_repo,
        team_member_repository=team_member_repo,
    )


@router.get("", response_model=ResponseSchema[list[CalendarRead]])
def get_my_calendars(
    current_user: User = Depends(get_current_active_user),
    service: CalendarService = Depends(get_calendar_service),
):
    """
    Get all calendars accessible by the current user.
    Includes personal calendar and team calendars.
    """
    result = service.get_my_calendars(current_user.id)
    return ResponseSchema(data=result)
