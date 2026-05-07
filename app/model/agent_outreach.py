from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.model.base_model import BaseModel

if TYPE_CHECKING:
    from app.model.task import Task
    from app.model.user import User


class AgentOutreach(BaseModel):
    __tablename__ = "agent_outreach"

    task_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("task.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("user.id"), nullable=False
    )

    outreach_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # 'missing_estimate' | 'missing_progress' | 'stale_update'

    channel: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # 'email' | 'telegram' | 'in_app'
    sent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    responded_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    response_type: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )  # 'updated_task' | 'ignored' | 'snoozed'

    # Relationships
    task: Mapped["Task"] = relationship("Task")
    user: Mapped["User"] = relationship("User")
