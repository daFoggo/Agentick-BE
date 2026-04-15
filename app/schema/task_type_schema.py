from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from app.schema.base_schema import FindBase, ModelBaseInfo


class TaskTypeBase(BaseModel):
    project_id: str
    name: str = Field(..., min_length=1, max_length=255)
    color: str = Field(..., pattern=r"^#[0-9A-Fa-f]{6}$")  # Hex color
    icon: Optional[str] = Field(None, max_length=255)
    order: float = Field(..., ge=0)
    is_default: bool = False


class TaskTypeCreate(TaskTypeBase):
    pass


class TaskTypeUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    color: Optional[str] = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")
    icon: Optional[str] = Field(None, max_length=255)
    order: Optional[float] = Field(None, ge=0)
    is_default: Optional[bool] = None


class TaskTypeRead(ModelBaseInfo, TaskTypeBase):
    model_config = ConfigDict(from_attributes=True)


class TaskTypeFind(FindBase):
    id__eq: Optional[str] = None
    project_id__eq: Optional[str] = None
    name__ilike: Optional[str] = None
    is_default__eq: Optional[bool] = None
