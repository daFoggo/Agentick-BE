from contextlib import nullcontext
from datetime import date

from fastapi import APIRouter, Depends

from app.core.dependencies import get_current_active_user, get_db
from app.model.user import User
from app.repository.calendar_repository import CalendarRepository
from app.repository.event_repository import EventRepository
from app.schema.base_schema import FindResult, ResponseSchema
from app.schema.event_schema import EventCreate, EventFind, EventRead, EventUpdate
from app.services.calendar_service import CalendarService
from app.repository.team_member_repository import TeamMemberRepository

router = APIRouter(prefix="/events", tags=["events"])


def get_calendar_service(db=Depends(get_db)) -> CalendarService:
    calendar_repo = CalendarRepository(lambda: nullcontext(db))
    event_repo = EventRepository(lambda: nullcontext(db))
    team_member_repo = TeamMemberRepository(lambda: nullcontext(db))
    return CalendarService(
        calendar_repository=calendar_repo,
        event_repository=event_repo,
        team_member_repository=team_member_repo,
    )


@router.get("/me", response_model=ResponseSchema[list[EventRead]])
def get_my_events(
    start_date: date | None = None,
    end_date: date | None = None,
    current_user: User = Depends(get_current_active_user),
    service: CalendarService = Depends(get_calendar_service),
):
    """
    Gather events from all teams for the current user.
    Aggregates all events where user_id == current_user.id.
    """
    result = service.get_my_events(
        user_id=current_user.id, start_date=start_date, end_date=end_date
    )
    return ResponseSchema(data=result)


@router.get("/teams/{team_id}", response_model=ResponseSchema[FindResult[EventRead]])
def get_team_events(
    team_id: str,
    find_query: EventFind = Depends(),
    current_user: User = Depends(get_current_active_user),
    service: CalendarService = Depends(get_calendar_service),
):
    """
    Get all events within a specific team.
    Filters events by team_id and date range.
    """
    result = service.get_team_events(team_id, find_query)
    return ResponseSchema(data=result)


@router.post("", response_model=ResponseSchema[EventRead])
def create_event(
    schema: EventCreate,
    current_user: User = Depends(get_current_active_user),
    service: CalendarService = Depends(get_calendar_service),
):
    # Ensure user_id is set to creator if not provided
    if not schema.user_id:
        schema.user_id = current_user.id

    result = service.create_event(schema)
    return ResponseSchema(data=result)


@router.patch("/{event_id}", response_model=ResponseSchema[EventRead])
def update_event(
    event_id: str,
    schema: EventUpdate,
    current_user: User = Depends(get_current_active_user),
    service: CalendarService = Depends(get_calendar_service),
):
    result = service.update_event(event_id, schema)
    return ResponseSchema(data=result)


@router.delete("/{event_id}", response_model=ResponseSchema[bool])
def delete_event(
    event_id: str,
    current_user: User = Depends(get_current_active_user),
    service: CalendarService = Depends(get_calendar_service),
):
    service.delete_event(event_id)
    return ResponseSchema(data=True)
