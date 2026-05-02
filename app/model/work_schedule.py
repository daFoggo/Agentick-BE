from sqlalchemy import Boolean, String, ForeignKey, Time, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.model.base_model import BaseModel


class WorkSchedule(BaseModel):
    __tablename__ = "work_schedule"

    team_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("team.id"), nullable=True)
    user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("user.id"), nullable=True)
    
    # 0 = Monday, 6 = Sunday (or 0=Sun, 6=Sat - keeping it consistent with ISO 0-6 where 0 is Mon)
    day_of_week: Mapped[int] = mapped_column(Integer, nullable=False)
    
    start_time: Mapped[str | None] = mapped_column(String(8), nullable=True)  # Format: "HH:MM"
    end_time: Mapped[str | None] = mapped_column(String(8), nullable=True)    # Format: "HH:MM"
    is_off: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    team: Mapped["Team | None"] = relationship("Team")
    user: Mapped["User | None"] = relationship("User")
