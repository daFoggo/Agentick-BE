from typing import Optional
from pydantic import BaseModel, ConfigDict
from app.schema.base_schema import ModelBaseInfo
from app.model.calendar import CalendarType


class CalendarBase(BaseModel):
    owner_id: str
    type: CalendarType
    name: Optional[str] = None
    description: Optional[str] = None


class CalendarCreate(CalendarBase):
    pass


class CalendarUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class CalendarRead(ModelBaseInfo, CalendarBase):
    model_config = ConfigDict(from_attributes=True)
