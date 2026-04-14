from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional
from app.schema.base_schema import FindBase, ModelBaseInfo
from app.schema.project_member_schema import ProjectMemberRead


class ProjectBase(BaseModel):
    team_id: str
    name: str = Field(..., min_length=3, max_length=255)
    description: Optional[str] = Field(None, max_length=512)
    avatar_url: Optional[str] = Field(None, max_length=512)


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=3, max_length=255)
    description: Optional[str] = Field(None, max_length=512)
    avatar_url: Optional[str] = Field(None, max_length=512)


class ProjectRead(ModelBaseInfo, ProjectBase):
    is_deleted: bool
    members: Optional[List[ProjectMemberRead]] = []

    model_config = ConfigDict(from_attributes=True)


class ProjectFind(FindBase):
    id__eq: Optional[str] = None
    team_id__eq: Optional[str] = None
    name__ilike: Optional[str] = None
    is_deleted__eq: Optional[bool] = False
