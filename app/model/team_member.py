from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import String, ForeignKey, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.model.base_model import BaseModel
from app.model.member_role import MemberRole

if TYPE_CHECKING:
    from app.model.team import Team
    from app.model.user import User


class TeamMember(BaseModel):
    __tablename__ = "team_member"

    team_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("team.id"), nullable=False
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("user.id"), nullable=False
    )
    role: Mapped[str] = mapped_column(
        String(50), default=MemberRole.MEMBER, nullable=False
    )
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    team: Mapped["Team"] = relationship("Team", back_populates="members")
    user: Mapped["User"] = relationship("User")
