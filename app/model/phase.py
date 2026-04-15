from datetime import datetime
from sqlalchemy import DateTime, String, ForeignKey, Float, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.model.base_model import BaseModel


class Phase(BaseModel):
    __tablename__ = "phase"

    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("project.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    order: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    start_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    end_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    project: Mapped["Project"] = relationship("Project")
    tasks: Mapped[list["Task"]] = relationship("Task", back_populates="phase")
