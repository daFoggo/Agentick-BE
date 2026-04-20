from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict
from app.schema.base_schema import ModelBaseInfo


class EventBase(BaseModel):
    calendar_id: str
    user_id: str
    team_id: str
    type: str  # task_block, meeting, focus_time, leave
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
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None


class EventRead(ModelBaseInfo, EventBase):
    model_config = ConfigDict(from_attributes=True)
