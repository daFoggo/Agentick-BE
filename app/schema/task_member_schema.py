from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.schema.base_schema import ModelBaseInfo
from app.schema.user_schema import UserRead


class TaskMemberBase(BaseModel):
    task_id: str
    user_id: str
    role: str = "member"  # 'lead' | 'member'


class TaskMemberCreate(TaskMemberBase):
    pass


class TaskMemberRead(ModelBaseInfo):
    task_id: str
    user_id: str
    role: str
    joined_at: datetime
    user: Optional[UserRead] = None

    model_config = ConfigDict(from_attributes=True)
