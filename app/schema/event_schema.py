from datetime import date, datetime
from typing import List, Optional

from app.model.event import EventType
from app.schema.base_schema import ModelBaseInfo
from pydantic import BaseModel, ConfigDict, Field, model_validator


class EventBase(BaseModel):
    user_id: str
    team_id: str
    type: EventType
    title: str
    description: Optional[str] = None
    start_time: datetime
    end_time: datetime
    participant_ids: Optional[List[str]] = Field(default_factory=list)


class EventCreate(EventBase):
    @model_validator(mode="after")
    def check_times(self) -> "EventCreate":
        if self.start_time >= self.end_time:
            raise ValueError("end_time must be after start_time")
        return self


class EventUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    type: Optional[EventType] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    participant_ids: Optional[List[str]] = None

    @model_validator(mode="after")
    def check_times(self) -> "EventUpdate":
        if self.start_time and self.end_time:
            if self.start_time >= self.end_time:
                raise ValueError("end_time must be after start_time")
        return self


from app.schema.team_member_schema import TeamMemberRead


class EventRead(ModelBaseInfo, EventBase):
    participants: Optional[List[TeamMemberRead]] = []
    model_config = ConfigDict(from_attributes=True)


from app.schema.base_schema import FindBase


class EventFind(FindBase):
    user_id__eq: Optional[str] = None
    team_id__eq: Optional[str] = None
    type__eq: Optional[EventType] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
