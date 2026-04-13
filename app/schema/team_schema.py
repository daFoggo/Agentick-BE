from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional

from app.schema.base_schema import FindBase, ModelBaseInfo


class TeamBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    description: Optional[str] = Field(None, max_length=512)
    avatar_url: Optional[str] = Field(None, max_length=512)


class TeamCreate(TeamBase):
    pass


class TeamUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    description: Optional[str] = Field(None, max_length=512)
    avatar_url: Optional[str] = Field(None, max_length=512)


class TeamRead(ModelBaseInfo, TeamBase):
    owner_id: str
    is_deleted: bool

    model_config = ConfigDict(from_attributes=True)


class TeamFind(FindBase):
    id__eq: Optional[str] = None
    name__ilike: Optional[str] = None
    owner_id__eq: Optional[str] = None
    is_deleted__eq: Optional[bool] = False
