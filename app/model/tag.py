from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.model.base_model import BaseModel


class Tag(BaseModel):
    __tablename__ = "tag"

    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("project.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    color: Mapped[str] = mapped_column(String(20), nullable=False)

    project: Mapped["Project"] = relationship("Project")
    tasks: Mapped[list["Task"]] = relationship("Task", secondary="task_tag", back_populates="tags")
