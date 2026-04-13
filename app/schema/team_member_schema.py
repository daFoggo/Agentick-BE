from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional

from app.schema.base_schema import FindBase, ModelBaseInfo
from app.schema.user_schema import UserRead


class TeamMemberBase(BaseModel):
    role: str = Field(..., pattern="^(owner|manager|member|viewer)$")


class TeamMemberCreate(TeamMemberBase):
    user_id: str


class TeamMemberUpdate(BaseModel):
    role: str = Field(..., pattern="^(owner|manager|member|viewer)$")


class TeamMemberRead(ModelBaseInfo, TeamMemberBase):
    team_id: str
    user_id: str
    joined_at: datetime
    user: Optional[UserRead] = None

    model_config = ConfigDict(from_attributes=True)


class TeamMemberFind(FindBase):
    team_id__eq: Optional[str] = None
    user_id__eq: Optional[str] = None
    role__eq: Optional[str] = None
