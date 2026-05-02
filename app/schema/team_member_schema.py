from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional

from app.schema.base_schema import FindBase, ModelBaseInfo
from app.schema.user_schema import UserRead
from app.model.member_role import MemberRole


class TeamMemberBase(BaseModel):
    role: MemberRole


class TeamMemberCreate(TeamMemberBase):
    user_id: str


class TeamMemberUpdate(BaseModel):
    role: MemberRole


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
    q: Optional[str] = None


class TeamMemberProjectCount(BaseModel):
    count: int


class TeamInviteGenerateRequest(BaseModel):
    email: str
    role: str = Field(..., pattern="^(owner|manager|member|viewer)$")


class TeamInviteTokenResponse(BaseModel):
    token: str


class TeamInviteAcceptRequest(BaseModel):
    token: str
