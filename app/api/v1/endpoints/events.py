from contextlib import nullcontext
from datetime import date
from typing import Any
from fastapi import APIRouter, Depends

from app.core.dependencies import get_db, get_current_active_user
from app.model.user import User
from app.repository.calendar_repository import CalendarRepository
from app.repository.event_repository import EventRepository
from app.repository.team_member_repository import TeamMemberRepository
from app.schema.base_schema import ResponseSchema
from app.schema.event_schema import EventCreate, EventRead, EventUpdate
from app.services.calendar_service import CalendarService

router = APIRouter(prefix="/events", tags=["events"])


def get_calendar_service(db=Depends(get_db)) -> CalendarService:
    calendar_repo = CalendarRepository(lambda: nullcontext(db))
    event_repo = EventRepository(lambda: nullcontext(db))
    return CalendarService(calendar_repository=calendar_repo, event_repository=event_repo)


@router.get("/me", response_model=ResponseSchema[list[EventRead]])
def get_my_events(
    start_date: date | None = None,
    end_date: date | None = None,
    current_user: User = Depends(get_current_active_user),
    db=Depends(get_db)
):
    """
    Gather events from all teams for the current user.
    Aggregates all events where user_id == current_user.id.
    """
    event_repo = EventRepository(lambda: nullcontext(db))
    
    options = {"user_id__eq": current_user.id}
    result = event_repo.read_by_options(options)["founds"]
    
    # Filter by range if provided
    if start_date and end_date:
        result = [
            e for e in result 
            if e.start_time and e.end_time and 
            e.start_time.date() <= end_date and e.end_time.date() >= start_date
        ]
        
    return ResponseSchema(data=result)


@router.get("/teams/{team_id}", response_model=ResponseSchema[list[EventRead]])
def get_team_events(
    team_id: str,
    start_date: date,
    end_date: date,
    current_user: User = Depends(get_current_active_user),
    db=Depends(get_db)
):
    """
    Get all events within a specific team.
    Filters events by team_id and date range.
    """
    event_repo = EventRepository(lambda: nullcontext(db))
    
    options = {"team_id__eq": team_id}
    result = event_repo.read_by_options(options)["founds"]
    
    # Filter by range
    result = [
        e for e in result 
        if e.start_time and e.end_time and 
        e.start_time.date() <= end_date and e.end_time.date() >= start_date
    ]
        
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
