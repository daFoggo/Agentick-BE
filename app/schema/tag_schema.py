from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from app.schema.base_schema import FindBase, ModelBaseInfo


class TagBase(BaseModel):
    project_id: str
    name: str = Field(..., min_length=1, max_length=255)
    color: str = Field(..., pattern=r"^#[0-9A-Fa-f]{6}$")  # Hex color


class TagCreate(TagBase):
    pass


class TagUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    color: Optional[str] = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")


class TagRead(ModelBaseInfo, TagBase):
    model_config = ConfigDict(from_attributes=True)


class TagFind(FindBase):
    id__eq: Optional[str] = None
    project_id__eq: Optional[str] = None
    name__ilike: Optional[str] = None
