from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, ConfigDict

from app.schema.base_schema import ModelBaseInfo
from app.schema.user_schema import UserRead


class TaskActivityBase(BaseModel):
    task_id: str
    activity_type: (
        str  # 'comment', 'field_change', 'status_change', 'started', 'completed'
    )
    field_name: Optional[str] = None
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    content: Optional[str] = None
    mentioned_user_ids: Optional[List[str]] = None


class TaskActivityCreate(BaseModel):
    task_id: str
    activity_type: str
    content: Optional[str] = None
    mentioned_user_ids: Optional[List[str]] = None


class TaskActivityRead(ModelBaseInfo):
    task_id: str
    user_id: str
    activity_type: str
    field_name: Optional[str] = None
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    content: Optional[str] = None
    is_edited: bool
    edited_at: Optional[datetime] = None
    mentioned_user_ids: Optional[List[str]] = None
    user: Optional[UserRead] = None

    model_config = ConfigDict(from_attributes=True)
