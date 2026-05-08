from typing import TYPE_CHECKING
from sqlalchemy import Boolean, ForeignKey, Integer, Float, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.model.base_model import BaseModel

if TYPE_CHECKING:
    from app.model.task import Task
    from app.model.user import User


class TaskCheckpoint(BaseModel):
    __tablename__ = "task_checkpoint"

    task_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("task.id", ondelete="CASCADE"), nullable=False
    )
    reported_by: Mapped[str] = mapped_column(
        String(36), ForeignKey("user.id"), nullable=False
    )

    progress_pct: Mapped[int] = mapped_column(Integer, nullable=False)
    is_blocked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    blocked_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    remaining_hours: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Relationships
    task: Mapped["Task"] = relationship("Task")
    reporter: Mapped["User"] = relationship("User", foreign_keys=[reported_by])
