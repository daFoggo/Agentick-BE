from typing import TYPE_CHECKING
from sqlalchemy import String, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from app.model.base_model import BaseModel

if TYPE_CHECKING:
    from app.model.user import User
    from app.model.team import Team
    from app.model.project import Project

class InvitationStatus(str, enum.Enum):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    DECLINED = "DECLINED"

class Invitation(BaseModel):
    __tablename__ = "invitation"

    email: Mapped[str] = mapped_column(String(255), nullable=False)
    inviter_id: Mapped[str] = mapped_column(String(36), ForeignKey("user.id"), nullable=False)
    team_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("team.id"), nullable=True)
    project_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("project.id"), nullable=True)
    role: Mapped[str] = mapped_column(String(50), default="member", nullable=False)
    status: Mapped[InvitationStatus] = mapped_column(SQLEnum(InvitationStatus), default=InvitationStatus.PENDING, nullable=False)

    inviter: Mapped["User"] = relationship("User", foreign_keys=[inviter_id])
    team: Mapped["Team"] = relationship("Team", foreign_keys=[team_id])
    project: Mapped["Project"] = relationship("Project", foreign_keys=[project_id])

    eagers = ["inviter", "team", "project"]
