from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.model.base_model import BaseModel

if TYPE_CHECKING:
    from app.model.task import Task
    from app.model.user import User


class TaskActivity(BaseModel):
    __tablename__ = "task_activity"

    task_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("task.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("user.id"), nullable=False
    )

    # 'comment' | 'field_change' | 'status_change' | 'member_add' | 'started' | 'completed' | 'checkpoint'
    activity_type: Mapped[str] = mapped_column(String(30), nullable=False)

    # For field_change
    field_name: Mapped[str | None] = mapped_column(String(50), nullable=True)
    old_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    new_value: Mapped[str | None] = mapped_column(Text, nullable=True)

    # For comments / system messages
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_edited: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    edited_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Mentions - store list of user IDs
    mentioned_user_ids: Mapped[list | None] = mapped_column(
        JSONB().with_variant(JSON(), "sqlite"), nullable=True
    )

    # Relationships
    task: Mapped["Task"] = relationship("Task")
    user: Mapped["User"] = relationship("User")

    eagers = ["user"]
