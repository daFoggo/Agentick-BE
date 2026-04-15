from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from app.schema.base_schema import FindBase, ModelBaseInfo


class TaskBase(BaseModel):
    project_id: str
    parent_id: Optional[str] = None
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    status_id: str
    type_id: str
    priority_id: str
    assigner_id: str
    assignee_id: Optional[str] = None
    phase_id: Optional[str] = None
    start_date: datetime
    due_date: datetime
    order: float = Field(..., ge=0)
    is_archived: bool = False
    is_deleted: bool = False


class TaskCreate(BaseModel):
    project_id: str
    parent_id: Optional[str] = None
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    status_id: str
    type_id: str
    priority_id: str
    assigner_id: str
    assignee_id: Optional[str] = None
    phase_id: Optional[str] = None
    start_date: datetime
    due_date: datetime
    order: Optional[float] = Field(None, ge=0)


class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    status_id: Optional[str] = None
    type_id: Optional[str] = None
    priority_id: Optional[str] = None
    assigner_id: Optional[str] = None
    assignee_id: Optional[str] = None
    phase_id: Optional[str] = None
    start_date: Optional[datetime] = None
    due_date: Optional[datetime] = None
    order: Optional[float] = Field(None, ge=0)
    is_archived: Optional[bool] = None


class TaskRead(ModelBaseInfo):
    project_id: str
    parent_id: Optional[str] = None
    title: str
    description: Optional[str] = None
    status_id: str
    type_id: str
    priority_id: str
    assigner_id: str
    assignee_id: Optional[str] = None
    phase_id: Optional[str] = None
    start_date: datetime
    due_date: datetime
    order: float
    is_archived: bool
    is_deleted: bool

    model_config = ConfigDict(from_attributes=True)


class TaskFind(FindBase):
    id__eq: Optional[str] = None
    project_id__eq: Optional[str] = None
    title__ilike: Optional[str] = None
    status_id__eq: Optional[str] = None
    assignee_id__eq: Optional[str] = None
    is_archived__eq: Optional[bool] = None
    is_deleted__eq: Optional[bool] = False
