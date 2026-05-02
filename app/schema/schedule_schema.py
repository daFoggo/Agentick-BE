from datetime import date
from typing import Optional
from pydantic import BaseModel, ConfigDict
from app.schema.base_schema import ModelBaseInfo


class WorkScheduleBase(BaseModel):
    team_id: Optional[str] = None
    user_id: Optional[str] = None
    day_of_week: int
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    is_off: bool = False


class WorkScheduleCreate(WorkScheduleBase):
    pass


class WorkScheduleUpdate(BaseModel):
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    is_off: Optional[bool] = None


class WorkScheduleRead(ModelBaseInfo, WorkScheduleBase):
    model_config = ConfigDict(from_attributes=True)
