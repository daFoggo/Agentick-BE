from typing import List, Optional
from app.repository.calendar_repository import CalendarRepository
from app.repository.event_repository import EventRepository
from app.schema.calendar_schema import CalendarCreate, CalendarRead
from app.schema.event_schema import EventCreate, EventRead, EventUpdate
from app.services.base_service import BaseService


class CalendarService(BaseService):
    def __init__(
        self,
        calendar_repository: CalendarRepository,
        event_repository: EventRepository,
    ) -> None:
        super().__init__(calendar_repository)
        self._calendar_repo = calendar_repository
        self._event_repo = event_repository

    def get_or_create_personal_calendar(self, user_id: str, user_name: str):
        calendars = self._calendar_repo.read_by_options(
            {"owner_id__eq": user_id, "type__eq": "personal"}
        )["founds"]
        
        if calendars:
            return calendars[0]
            
        schema = CalendarCreate(
            owner_id=user_id,
            type="personal",
            name=f"{user_name}'s Focus Calendar",
            description="Automatic focus calendar for tasks and personal events."
        )
        return self._calendar_repo.create(schema)

    def get_or_create_team_calendar(self, team_id: str, team_name: str):
        calendars = self._calendar_repo.read_by_options(
            {"owner_id__eq": team_id, "type__eq": "team"}
        )["founds"]
        
        if calendars:
            return calendars[0]
            
        schema = CalendarCreate(
            owner_id=team_id,
            type="team",
            name=f"{team_name}'s Shared Calendar",
            description="Team events and shared schedules."
        )
        return self._calendar_repo.create(schema)


    def create_event(self, schema: EventCreate):
        return self._event_repo.create(schema)

    def update_event(self, event_id: str, schema: EventUpdate):
        return self._event_repo.update(event_id, schema)

    def delete_event(self, event_id: str):
        return self._event_repo.delete_by_id(event_id)

    def delete_task_event(self, task_id: str):
        events = self._event_repo.read_by_options({"task_id__eq": task_id})["founds"]
        for event in events:
            self._event_repo.delete_by_id(event.id)
