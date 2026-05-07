from contextlib import nullcontext
from datetime import datetime, timedelta, timezone
from typing import List, Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, distinct

from app.core.dependencies import get_current_active_user, get_db
from app.core.exceptions import DuplicatedError
from app.model.user import User
from app.model.task import Task, task_assignee
from app.model.project_member import ProjectMember
from app.model.task_status import TaskStatus
from app.repository.project_member_repository import ProjectMemberRepository
from app.repository.project_repository import ProjectRepository
from app.repository.team_member_repository import TeamMemberRepository
from app.repository.team_repository import TeamRepository
from app.repository.task_status_repository import TaskStatusRepository
from app.repository.task_type_repository import TaskTypeRepository
from app.repository.task_priority_repository import TaskPriorityRepository
from app.schema.base_schema import FindResult, ResponseSchema
from app.schema.project_member_schema import (
    ProjectMemberCreate,
    ProjectMemberRead,
    ProjectMemberUpdate,
    ProjectInviteGenerateRequest,
    ProjectInviteTokenResponse,
    ProjectInviteAcceptRequest,
)
from app.schema.project_schema import ProjectCreate, ProjectFind, ProjectRead, ProjectUpdate
from app.schema.task_schema import TaskRead, MemberWorkload, ProjectWorkloadResponse, WorkloadDataPoint
from app.services.project_member_service import ProjectMemberService
from app.services.project_service import ProjectService
from app.services.invitation_service import InvitationService
from app.api.v1.endpoints.invitations import get_invitation_service
from app.services.task_service import TaskService
from app.api.v1.endpoints.project_tasks import get_task_service

router = APIRouter(prefix="/projects", tags=["projects"])


def get_project_service(db=Depends(get_db)) -> ProjectService:
    project_repository = ProjectRepository(lambda: nullcontext(db))
    project_member_repository = ProjectMemberRepository(lambda: nullcontext(db))
    team_repository = TeamRepository(lambda: nullcontext(db))
    team_member_repository = TeamMemberRepository(lambda: nullcontext(db))
    task_status_repository = TaskStatusRepository(lambda: nullcontext(db))
    task_type_repository = TaskTypeRepository(lambda: nullcontext(db))
    task_priority_repository = TaskPriorityRepository(lambda: nullcontext(db))
    return ProjectService(
        project_repository=project_repository,
        team_repository=team_repository,
        team_member_repository=team_member_repository,
        project_member_repository=project_member_repository,
        task_status_repository=task_status_repository,
        task_type_repository=task_type_repository,
        task_priority_repository=task_priority_repository,
    )


def get_project_member_service(db=Depends(get_db)) -> ProjectMemberService:
    project_member_repository = ProjectMemberRepository(lambda: nullcontext(db))
    project_repository = ProjectRepository(lambda: nullcontext(db))
    team_member_repository = TeamMemberRepository(lambda: nullcontext(db))
    return ProjectMemberService(
        project_member_repository=project_member_repository,
        project_repository=project_repository,
        team_member_repository=team_member_repository,
    )


@router.post("", response_model=ResponseSchema[ProjectRead])
def create_project(
    schema: ProjectCreate,
    current_user: User = Depends(get_current_active_user),
    service: ProjectService = Depends(get_project_service),
):
    result = service.create_project(schema, current_user)
    return ResponseSchema(data=result, message="Project created successfully")


@router.get("", response_model=ResponseSchema[FindResult[ProjectRead]])
def get_projects(
    find_query: ProjectFind = Depends(),
    current_user: User = Depends(get_current_active_user),
    service: ProjectService = Depends(get_project_service),
):
    result = service.get_projects(find_query, current_user)
    return ResponseSchema(data=result)


@router.get("/me", response_model=ResponseSchema[List[ProjectRead]])
def get_my_projects(
    current_user: User = Depends(get_current_active_user),
    service: ProjectService = Depends(get_project_service),
):
    result = service.get_my_projects(current_user.id)
    return ResponseSchema(data=result)


@router.get("/{project_id}", response_model=ResponseSchema[ProjectRead])
def get_project(
    project_id: str,
    current_user: User = Depends(get_current_active_user),
    service: ProjectService = Depends(get_project_service),
):
    result = service.get_project_details(project_id, current_user)
    return ResponseSchema(data=result)


@router.patch("/{project_id}", response_model=ResponseSchema[ProjectRead])
def update_project(
    project_id: str,
    schema: ProjectUpdate,
    current_user: User = Depends(get_current_active_user),
    service: ProjectService = Depends(get_project_service),
):
    result = service.update_project(project_id, schema, current_user)
    return ResponseSchema(data=result, message="Project updated successfully")


@router.delete("/{project_id}", response_model=ResponseSchema[bool])
def delete_project(
    project_id: str,
    current_user: User = Depends(get_current_active_user),
    service: ProjectService = Depends(get_project_service),
):
    service.delete_project(project_id, current_user)
    return ResponseSchema(data=True, message="Project deleted successfully")


@router.get("/{project_id}/members", response_model=ResponseSchema[FindResult[ProjectMemberRead]])
def get_project_members(
    project_id: str,
    current_user: User = Depends(get_current_active_user),
    service: ProjectMemberService = Depends(get_project_member_service),
):
    result = service.get_members(project_id, current_user)
    return ResponseSchema(data=result)


@router.post("/{project_id}/members", response_model=ResponseSchema[ProjectMemberRead])
def add_project_member(
    project_id: str,
    schema: ProjectMemberCreate,
    current_user: User = Depends(get_current_active_user),
    service: ProjectMemberService = Depends(get_project_member_service),
):
    result = service.add_member(project_id, schema, current_user)
    return ResponseSchema(data=result, message="Member added successfully")


@router.patch("/{project_id}/members/{user_id}", response_model=ResponseSchema[ProjectMemberRead])
def update_project_member(
    project_id: str,
    user_id: str,
    schema: ProjectMemberUpdate,
    current_user: User = Depends(get_current_active_user),
    service: ProjectMemberService = Depends(get_project_member_service),
):
    result = service.update_member_role(project_id, user_id, schema, current_user)
    return ResponseSchema(data=result, message="Member role updated successfully")


@router.delete("/{project_id}/members/{user_id}", response_model=ResponseSchema[bool])
def remove_project_member(
    project_id: str,
    user_id: str,
    current_user: User = Depends(get_current_active_user),
    service: ProjectMemberService = Depends(get_project_member_service),
):
    service.remove_member(project_id, user_id, current_user)
    return ResponseSchema(data=True, message="Member removed successfully")


@router.post("/{project_id}/invitations/generate", response_model=ResponseSchema[ProjectInviteTokenResponse])
def generate_project_invitation(
    project_id: str,
    schema: ProjectInviteGenerateRequest,
    current_user: User = Depends(get_current_active_user),
    project_service: ProjectService = Depends(get_project_service),
    project_member_service: ProjectMemberService = Depends(get_project_member_service),
    invitation_service: InvitationService = Depends(get_invitation_service)
):
    project_member_service.check_permission(project_id, current_user.id, "manager")
    
    project = project_service.get_project_details(project_id, current_user)
    
    # Check if user with this email is already a member
    target_user = invitation_service.user_repository.read_by_email(schema.email)
    if target_user and project_member_service.is_user_member(project_id, target_user.id):
        raise DuplicatedError(detail=f"User with email {schema.email} is already a member of this project.")

    invitation = invitation_service.create_and_send_invitation(
        email=schema.email,
        inviter=current_user,
        role=schema.role,
        project_id=project_id,
        team_id=project.team_id,
        target_name=project.name
    )
    return ResponseSchema(data=ProjectInviteTokenResponse(token=invitation.id), message="Invitation sent successfully")


@router.post("/invitations/accept", response_model=ResponseSchema[ProjectMemberRead])
def accept_project_invitation(
    schema: ProjectInviteAcceptRequest,
    current_user: User = Depends(get_current_active_user),
    service: ProjectMemberService = Depends(get_project_member_service)
):
    result = service.accept_invite_token(schema.token, current_user)
    return ResponseSchema(data=result, message="Successfully joined the project")


@router.get("/{project_id}/gantt", response_model=ResponseSchema[List[TaskRead]])
def get_project_gantt(
    project_id: str,
    current_user: User = Depends(get_current_active_user),
    task_service: TaskService = Depends(get_task_service),
):
    result = task_service.get_gantt_data(project_id)
    return ResponseSchema(data=result)


@router.get("/{project_id}/members/workload", response_model=ResponseSchema[ProjectWorkloadResponse])
def get_project_member_workload(
    project_id: str,
    period: Literal["weekly", "monthly"] = Query(default="weekly"),
    current_user: User = Depends(get_current_active_user),
    db=Depends(get_db),
):
    """
    Workload của từng member trong project — số task/ngày theo tuần hoặc tháng.
    Dùng cho biểu đồ ProjectWorkload trên Dashboard.
    """
    from sqlalchemy import cast, Date as SADate

    now = datetime.now(timezone.utc)

    # weekly = 7 ngày qua, monthly = 30 ngày qua
    delta = timedelta(days=7) if period == "weekly" else timedelta(days=30)
    date_from = now - delta
    date_to = now

    # Lấy tất cả member của project (join với user để lấy thông tin)
    from sqlalchemy.orm import joinedload
    members = (
        db.query(ProjectMember)
        .options(joinedload(ProjectMember.user))
        .filter(ProjectMember.project_id == project_id)
        .all()
    )

    result_members: list[MemberWorkload] = []

    for member in members:
        user = member.user

        # Convert UTC → local time (Asia/Ho_Chi_Minh = UTC+7) trước khi cast sang Date
        # để tránh lệch ngày với task được done lúc trước 7am Vietnam time
        local_day_expr = cast(
            func.timezone("Asia/Ho_Chi_Minh", Task.updated_at), SADate
        ).label("day")

        # Query: đếm task DONE được assign cho member, nhóm theo ngày local
        rows = (
            db.query(
                local_day_expr,
                func.count(distinct(Task.id)).label("task_count"),
            )
            .join(task_assignee, task_assignee.c.task_id == Task.id)
            .join(TaskStatus, Task.status_id == TaskStatus.id)
            .filter(
                Task.project_id == project_id,
                task_assignee.c.project_member_id == member.id,
                Task.is_deleted.is_(False),
                Task.is_archived.is_(False),
                # Lấy task done: is_completed=True HOẶC tên status là "Done" (fallback)
                (TaskStatus.is_completed.is_(True) | (func.lower(TaskStatus.name) == "done")),
                Task.updated_at >= date_from,
                Task.updated_at < date_to,
            )
            .group_by(local_day_expr)
            .order_by(local_day_expr)
            .all()
        )

        # Map từ DB → dict để lookup nhanh
        count_by_day: dict[str, int] = {str(row.day): row.task_count for row in rows}

        # Fill đầy đủ mỗi ngày trong range (kể cả ngày = 0 task done)
        # Dùng local date (UTC+7) để tránh lệch ngày
        vn_offset = timedelta(hours=7)
        local_start = (date_from + vn_offset).date()
        local_end   = (date_to + vn_offset).date() + timedelta(days=1)  # inclusive today

        series: list[WorkloadDataPoint] = []
        current_day = local_start
        while current_day < local_end:
            day_str = current_day.isoformat()
            series.append(
                WorkloadDataPoint(date=day_str, task_count=count_by_day.get(day_str, 0))
            )
            current_day += timedelta(days=1)

        result_members.append(
            MemberWorkload(
                user_id=user.id,
                name=user.name,
                avatar_url=user.avatar_url,
                series=series,
            )
        )

    return ResponseSchema(
        data=ProjectWorkloadResponse(
            members=result_members,
            period=period,
            date_from=date_from.date().isoformat(),
            date_to=date_to.date().isoformat(),
        ),
        message="Member workload fetched successfully",
    )
