from typing import Any
from app.repository.calendar_repository import CalendarRepository
from app.repository.event_repository import EventRepository
from app.schema.calendar_schema import CalendarCreate
from app.schema.event_schema import EventCreate, EventUpdate
from app.services.base_service import BaseService


class CalendarService(BaseService):
    def __init__(
        self,
        calendar_repository: CalendarRepository,
        event_repository: EventRepository,
        team_member_repository: Any = None,
    ) -> None:
        super().__init__(calendar_repository)
        self._calendar_repo = calendar_repository
        self._event_repo = event_repository
        self._team_member_repo = team_member_repository

    def get_my_calendars(self, user_id: str):
        """
        Get all calendars accessible by the user.
        """
        if not self._team_member_repo:
            return []

        team_members = self._team_member_repo.read_by_options({"user_id__eq": user_id})[
            "founds"
        ]
        team_ids = [tm.team_id for tm in team_members]

        personal_calendars = self._calendar_repo.read_by_options(
            {"owner_id__eq": user_id, "type__eq": "personal"}
        )["founds"]

        team_calendars = []
        if team_ids:
            for t_id in team_ids:
                tc = self._calendar_repo.read_by_options(
                    {"owner_id__eq": t_id, "type__eq": "team"}
                )["founds"]
                team_calendars.extend(tc)

        return personal_calendars + team_calendars

    def get_my_events(self, user_id: str, start_date=None, end_date=None):
        options = {"user_id__eq": user_id}
        result = self._event_repo.read_by_options(options)["founds"]

        if start_date and end_date:
            result = [
                e
                for e in result
                if e.start_time
                and e.end_time
                and e.start_time.date() <= end_date
                and e.end_time.date() >= start_date
            ]
        return result

    def get_team_events(self, team_id: str, find_query: Any):
        find_query.team_id__eq = team_id
        options = find_query.model_dump(exclude_none=True)

        start_date = options.pop("start_date", None)
        end_date = options.pop("end_date", None)

        result = self._event_repo.read_by_options(options)

        if start_date or end_date:
            filtered = result["founds"]
            if start_date:
                filtered = [e for e in filtered if e.end_time.date() >= start_date]
            if end_date:
                filtered = [e for e in filtered if e.start_time.date() <= end_date]
            result["founds"] = filtered

        return result

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
            description="Automatic focus calendar for tasks and personal events.",
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
            description="Team events and shared schedules.",
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
