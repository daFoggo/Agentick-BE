from datetime import datetime
from sqlalchemy import Boolean, DateTime, Float, String, ForeignKey, Text, Column, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.model.base_model import BaseModel


task_tag = Table(
    "task_tag",
    BaseModel.metadata,
    Column("task_id", String(36), ForeignKey("task.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", String(36), ForeignKey("tag.id", ondelete="CASCADE"), primary_key=True),
)


class Task(BaseModel):
    __tablename__ = "task"

    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("project.id"), nullable=False)
    parent_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("task.id"), nullable=True)
    
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    status_id: Mapped[str] = mapped_column(String(36), ForeignKey("task_status.id"), nullable=False)
    type_id: Mapped[str] = mapped_column(String(36), ForeignKey("task_type.id"), nullable=False)
    priority_id: Mapped[str] = mapped_column(String(36), ForeignKey("task_priority.id"), nullable=False)
    
    assigner_id: Mapped[str] = mapped_column(String(36), ForeignKey("project_member.id"), nullable=False)
    assignee_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("project_member.id"), nullable=True)
    
    phase_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("phase.id"), nullable=True)
    
    start_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    due_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    
    order: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    project: Mapped["Project"] = relationship("Project")
    status: Mapped["TaskStatus"] = relationship("TaskStatus")
    type: Mapped["TaskType"] = relationship("TaskType")
    priority: Mapped["TaskPriority"] = relationship("TaskPriority")
    assigner: Mapped["ProjectMember"] = relationship("ProjectMember", foreign_keys=[assigner_id])
    assignee: Mapped["ProjectMember | None"] = relationship("ProjectMember", foreign_keys=[assignee_id])
    phase: Mapped["Phase"] = relationship("Phase", back_populates="tasks")
    tags: Mapped[list["Tag"]] = relationship("Tag", secondary=task_tag, back_populates="tasks")
    parent: Mapped["Task | None"] = relationship("Task", back_populates="sub_tasks", remote_side="Task.id")
    sub_tasks: Mapped[list["Task"]] = relationship("Task", back_populates="parent")

    eagers = ["status", "type", "priority", "assignee", "tags"]
