from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from app.schema.base_schema import FindBase, ModelBaseInfo


class TaskPriorityBase(BaseModel):
    project_id: str
    name: str = Field(..., min_length=1, max_length=255)
    color: str = Field(..., pattern=r"^#[0-9A-Fa-f]{6}$")  # Hex color
    level: int = Field(..., ge=0, le=3)  # 0 (low) to 3 (urgent)
    order: float = Field(..., ge=0)
    is_default: bool = False


class TaskPriorityCreate(TaskPriorityBase):
    pass


class TaskPriorityUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    color: Optional[str] = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")
    level: Optional[int] = Field(None, ge=0, le=3)
    order: Optional[float] = Field(None, ge=0)
    is_default: Optional[bool] = None


class TaskPriorityRead(ModelBaseInfo, TaskPriorityBase):
    model_config = ConfigDict(from_attributes=True)


class TaskPriorityFind(FindBase):
    id__eq: Optional[str] = None
    project_id__eq: Optional[str] = None
    name__ilike: Optional[str] = None
    level__eq: Optional[int] = None
    is_default__eq: Optional[bool] = None
