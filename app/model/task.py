from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, String, Table, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.model.base_model import BaseModel

if TYPE_CHECKING:
    from app.model.phase import Phase
    from app.model.project import Project
    from app.model.tag import Tag
    from app.model.task_member import TaskMember
    from app.model.task_priority import TaskPriority
    from app.model.task_status import TaskStatus
    from app.model.task_type import TaskType


task_tag = Table(
    "task_tag",
    BaseModel.metadata,
    Column(
        "task_id",
        String(36),
        ForeignKey("task.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "tag_id", String(36), ForeignKey("tag.id", ondelete="CASCADE"), primary_key=True
    ),
)


class Task(BaseModel):
    __tablename__ = "task"

    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("project.id"), nullable=False
    )
    parent_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("task.id"), nullable=True
    )

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    status_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("task_status.id"), nullable=False
    )
    type_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("task_type.id"), nullable=False
    )
    priority_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("task_priority.id"), nullable=False
    )

    phase_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("phase.id"), nullable=True
    )

    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    due_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    order: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    estimated_hours: Mapped[float | None] = mapped_column(Float, nullable=True)
    actual_hours: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    project: Mapped["Project"] = relationship("Project")
    status: Mapped["TaskStatus"] = relationship("TaskStatus")
    type: Mapped["TaskType"] = relationship("TaskType")
    priority: Mapped["TaskPriority"] = relationship("TaskPriority")

    task_members: Mapped[list["TaskMember"]] = relationship(
        "TaskMember", back_populates="task", cascade="all, delete-orphan"
    )

    phase: Mapped["Phase"] = relationship("Phase", back_populates="tasks")
    tags: Mapped[list["Tag"]] = relationship(
        "Tag", secondary=task_tag, back_populates="tasks"
    )
    parent: Mapped["Task | None"] = relationship(
        "Task", back_populates="sub_tasks", remote_side="Task.id"
    )
    sub_tasks: Mapped[list["Task"]] = relationship("Task", back_populates="parent")

    eagers = ["status", "type", "priority", "tags", "task_members"]
