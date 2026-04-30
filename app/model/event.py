from enum import Enum
from datetime import datetime
from sqlalchemy import DateTime, String, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.model.base_model import BaseModel


class EventType(str, Enum):
    TASK = "task"
    MEETING = "meeting"
    FOCUS_TIME = "focus_time"
    LEAVE = "leave"


class Event(BaseModel):
    __tablename__ = "event"

    calendar_id: Mapped[str] = mapped_column(String(36), ForeignKey("calendar.id"), nullable=False)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("user.id"), nullable=False)
    team_id: Mapped[str] = mapped_column(String(36), ForeignKey("team.id"), nullable=False, index=True)
    
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    
    # Optional link to a task
    task_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("task.id", ondelete="CASCADE"), nullable=True)

    # Relationships
    calendar: Mapped["Calendar"] = relationship("Calendar")
    task: Mapped["Task | None"] = relationship("Task")
    user: Mapped["User"] = relationship("User")
    team: Mapped["Team"] = relationship("Team")
