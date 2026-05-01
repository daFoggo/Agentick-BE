from enum import Enum
from datetime import datetime
from sqlalchemy import DateTime, String, ForeignKey, Text, Column, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.model.base_model import BaseModel


class EventType(str, Enum):
    MEETING = "meeting"
    FOCUS_TIME = "focus_time"
    LEAVE = "leave"


event_participant = Table(
    "event_participant",
    BaseModel.metadata,
    Column("event_id", String(36), ForeignKey("event.id", ondelete="CASCADE"), primary_key=True),
    Column("team_member_id", String(36), ForeignKey("team_member.id", ondelete="CASCADE"), primary_key=True),
)


class Event(BaseModel):
    __tablename__ = "event"

    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("user.id"), nullable=False)
    team_id: Mapped[str] = mapped_column(String(36), ForeignKey("team.id"), nullable=False, index=True)
    
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    

    # Relationships
    user: Mapped["User"] = relationship("User")
    team: Mapped["Team"] = relationship("Team")
    participants: Mapped[list["TeamMember"]] = relationship("TeamMember", secondary=event_participant)
    
    @property
    def participant_ids(self) -> list[str]:
        return [p.id for p in self.participants]

    eagers = ["participants"]
