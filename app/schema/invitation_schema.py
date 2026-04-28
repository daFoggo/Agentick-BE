from datetime import datetime
from pydantic import BaseModel, ConfigDict
from app.model.invitation import InvitationStatus
from app.schema.user_schema import UserRead
from app.schema.team_schema import TeamRead
from app.schema.project_schema import ProjectRead

class InvitationResponse(BaseModel):
    id: str
    email: str
    inviter_id: str
    team_id: str | None = None
    project_id: str | None = None
    role: str
    status: InvitationStatus
    created_at: datetime
    updated_at: datetime

    inviter: UserRead | None = None
    team: TeamRead | None = None
    project: ProjectRead | None = None

    model_config = ConfigDict(from_attributes=True)
