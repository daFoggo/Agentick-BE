from __future__ import annotations

from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field, ConfigDict

from app.schema.base_schema import FindBase, ModelBaseInfo
from app.schema.task_status_schema import TaskStatusRead
from app.schema.task_type_schema import TaskTypeRead
from app.schema.task_priority_schema import TaskPriorityRead

from app.schema.task_member_schema import TaskMemberRead


class TaskBase(BaseModel):
    project_id: str
    parent_id: Optional[str] = None
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    status_id: str
    type_id: str
    priority_id: str
    member_ids: Optional[List[str]] = None
    phase_id: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    due_date: datetime
    order: float = Field(..., ge=0)
    estimated_hours: Optional[float] = None
    actual_hours: float = 0.0
    is_archived: bool = False
    is_deleted: bool = False


class TaskCreate(BaseModel):
    project_id: str
    parent_id: Optional[str] = None
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    status_id: str
    type_id: str
    priority_id: str
    member_ids: Optional[List[str]] = None
    phase_id: Optional[str] = None
    started_at: Optional[datetime] = None
    due_date: datetime
    order: Optional[float] = Field(None, ge=0)
    estimated_hours: Optional[float] = None


class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    status_id: Optional[str] = None
    type_id: Optional[str] = None
    priority_id: Optional[str] = None
    member_ids: Optional[List[str]] = None
    phase_id: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    due_date: Optional[datetime] = None
    order: Optional[float] = Field(None, ge=0)
    is_archived: Optional[bool] = None
    estimated_hours: Optional[float] = None
    actual_hours: Optional[float] = None


class TaskRead(ModelBaseInfo):
    project_id: str
    parent_id: Optional[str] = None
    title: str
    description: Optional[str] = None
    status_id: str
    type_id: str
    priority_id: str
    member_ids: Optional[List[str]] = None
    phase_id: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    due_date: Optional[datetime] = None
    order: float
    estimated_hours: Optional[float] = None
    actual_hours: float
    is_archived: bool
    is_deleted: bool
    task_members: Optional[List[TaskMemberRead]] = []
    status: Optional[TaskStatusRead] = None
    type: Optional[TaskTypeRead] = None
    priority: Optional[TaskPriorityRead] = None

    model_config = ConfigDict(from_attributes=True)


class MyTasksOverview(BaseModel):
    in_progress: List[TaskRead]
    upcoming: List[TaskRead]
    overdue: List[TaskRead]

    model_config = ConfigDict(from_attributes=True)


class TaskFind(FindBase):
    id__eq: Optional[str] = None
    project_id__eq: Optional[str] = None
    team_id__eq: Optional[str] = None
    title__ilike: Optional[str] = None
    status_id__eq: Optional[str] = None
    # Filter by any of the members containing this ID
    member_ids__contains: Optional[str] = None
    is_archived__eq: Optional[bool] = None
    is_deleted__eq: Optional[bool] = False
    # Dashboard Overview: filter tasks assigned to a specific user (by user.id)
    member_user_id__eq: Optional[str] = None


# ── Dashboard: Task Stats ─────────────────────────────────────────────────────


class TaskStatItem(BaseModel):
    """Một nhóm thống kê (priority / status / type) với số lượng task."""

    id: str
    name: str
    color: str
    count: int

    model_config = ConfigDict(from_attributes=True)


class ProjectTaskStats(BaseModel):
    """Response cho GET /projects/{project_id}/tasks/stats"""

    by_priority: List[TaskStatItem]
    by_status: List[TaskStatItem]
    by_type: List[TaskStatItem]
    period: str  # "weekly" | "monthly"
    date_from: str  # ISO date string
    date_to: str  # ISO date string


# ── Dashboard: Member Workload ────────────────────────────────────────────────


class WorkloadDataPoint(BaseModel):
    """Số task của một member trong một ngày cụ thể."""

    date: str  # "YYYY-MM-DD"
    task_count: int


class MemberWorkload(BaseModel):
    """Workload series của một member trong project."""

    user_id: str
    name: str
    avatar_url: Optional[str] = None
    series: List[WorkloadDataPoint]

    model_config = ConfigDict(from_attributes=True)


class ProjectWorkloadResponse(BaseModel):
    """Response cho GET /projects/{project_id}/members/workload"""

    members: List[MemberWorkload]
    period: str  # "weekly" | "monthly"
    date_from: str
    date_to: str
