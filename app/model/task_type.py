from sqlalchemy import Boolean, String, ForeignKey, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.model.base_model import BaseModel


class TaskType(BaseModel):
    __tablename__ = "task_type"

    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("project.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    color: Mapped[str] = mapped_column(String(20), nullable=False)
    icon: Mapped[str | None] = mapped_column(String(100), nullable=True)
    order: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    project: Mapped["Project"] = relationship("Project")
