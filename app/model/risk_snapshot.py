from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.model.base_model import BaseModel

if TYPE_CHECKING:
    from app.model.task import Task


class RiskSnapshot(BaseModel):
    __tablename__ = "risk_snapshot"

    task_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("task.id", ondelete="CASCADE"), nullable=False
    )

    risk_score: Mapped[float] = mapped_column(Float, nullable=False)  # 0.0 -> 1.0
    risk_level: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # 'low' | 'medium' | 'high' | 'critical'
    alert_type: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )  # 'data_gap' | 'stale' | 'high_risk'

    signals: Mapped[dict | list | None] = mapped_column(JSON, nullable=True)
    recommendation: Mapped[str | None] = mapped_column(Text, nullable=True)

    predicted_completion_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    alert_sent: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    alert_sent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    actual_completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    prediction_error_hours: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Relationships
    task: Mapped["Task"] = relationship("Task")

    def __repr__(self) -> str:
        import json
        data = {
            "task_id": self.task_id,
            "risk_score": self.risk_score,
            "risk_level": self.risk_level,
            "alert_type": self.alert_type,
            "recommendation": self.recommendation,
            "signals": self.signals,
            "alert_sent": self.alert_sent,
        }
        return json.dumps(data, indent=2, ensure_ascii=False)
