from sqlalchemy import Boolean, String, ForeignKey, Float, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.model.base_model import BaseModel


class TaskPriority(BaseModel):
    __tablename__ = "task_priority"

    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("project.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    color: Mapped[str] = mapped_column(String(20), nullable=False)
    level: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    order: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    project: Mapped["Project"] = relationship("Project")
