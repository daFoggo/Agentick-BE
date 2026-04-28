from datetime import datetime
from sqlalchemy import String, ForeignKey, DateTime, func, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from app.model.base_model import BaseModel

class InvitationStatus(str, enum.Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"

class Invitation(BaseModel):
    __tablename__ = "invitation"

    email: Mapped[str] = mapped_column(String(255), nullable=False)
    inviter_id: Mapped[str] = mapped_column(String(36), ForeignKey("user.id"), nullable=False)
    team_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("team.id"), nullable=True)
    project_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("project.id"), nullable=True)
    role: Mapped[str] = mapped_column(String(50), default="member", nullable=False)
    status: Mapped[InvitationStatus] = mapped_column(SQLEnum(InvitationStatus), default=InvitationStatus.PENDING, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    inviter: Mapped["User"] = relationship("User", foreign_keys=[inviter_id])
    team: Mapped["Team"] = relationship("Team", foreign_keys=[team_id])
    project: Mapped["Project"] = relationship("Project", foreign_keys=[project_id])

    eagers = ["inviter", "team", "project"]
