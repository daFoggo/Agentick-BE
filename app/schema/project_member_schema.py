from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.schema.base_schema import FindBase, ModelBaseInfo
from app.schema.user_schema import UserRead


class ProjectMemberBase(BaseModel):
    role: str = Field(..., pattern="^(owner|manager|member|viewer)$")


class ProjectMemberCreate(ProjectMemberBase):
    user_id: str


class ProjectMemberUpdate(BaseModel):
    role: str = Field(..., pattern="^(owner|manager|member|viewer)$")


class ProjectMemberRead(ModelBaseInfo, ProjectMemberBase):
    project_id: str
    user_id: str
    joined_at: datetime
    user: Optional[UserRead] = None

    model_config = ConfigDict(from_attributes=True)


class ProjectMemberFind(FindBase):
    project_id__eq: Optional[str] = None
    user_id__eq: Optional[str] = None
    role__eq: Optional[str] = None
