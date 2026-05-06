from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.model.base_model import BaseModel
from app.model.member_role import MemberRole

if TYPE_CHECKING:
    from app.model.project import Project
    from app.model.user import User



class ProjectMember(BaseModel):
    __tablename__ = "project_member"

    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("project.id"), nullable=False
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

    project: Mapped["Project"] = relationship("Project", back_populates="members")
    user: Mapped["User"] = relationship("User")

    eagers = ["user"]
