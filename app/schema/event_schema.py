from datetime import datetime, date
from typing import Optional
from pydantic import BaseModel, ConfigDict
from app.schema.base_schema import ModelBaseInfo
from app.model.event import EventType


class EventBase(BaseModel):
    calendar_id: str
    user_id: str
    team_id: str
    type: EventType
    title: str
    description: Optional[str] = None
    start_time: datetime
    end_time: datetime
    task_id: Optional[str] = None


class EventCreate(EventBase):
    pass


class EventUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    type: Optional[EventType] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None


class EventRead(ModelBaseInfo, EventBase):
    model_config = ConfigDict(from_attributes=True)


from app.schema.base_schema import FindBase


class EventFind(FindBase):
    user_id__eq: Optional[str] = None
    team_id__eq: Optional[str] = None
    calendar_id__eq: Optional[str] = None
    type__eq: Optional[EventType] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
