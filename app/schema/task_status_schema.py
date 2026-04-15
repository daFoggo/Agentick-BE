from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from app.schema.base_schema import FindBase, ModelBaseInfo


class TaskStatusBase(BaseModel):
    project_id: str
    name: str = Field(..., min_length=1, max_length=255)
    color: str = Field(..., pattern=r"^#[0-9A-Fa-f]{6}$")  # Hex color
    order: float = Field(..., ge=0)
    is_default: bool = False
    is_completed: bool = False


class TaskStatusCreate(TaskStatusBase):
    pass


class TaskStatusUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    color: Optional[str] = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")
    order: Optional[float] = Field(None, ge=0)
    is_default: Optional[bool] = None
    is_completed: Optional[bool] = None


class TaskStatusRead(ModelBaseInfo, TaskStatusBase):
    model_config = ConfigDict(from_attributes=True)


class TaskStatusFind(FindBase):
    id__eq: Optional[str] = None
    project_id__eq: Optional[str] = None
    name__ilike: Optional[str] = None
    is_default__eq: Optional[bool] = None
    is_completed__eq: Optional[bool] = None
