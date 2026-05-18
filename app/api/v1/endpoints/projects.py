from contextlib import nullcontext
from typing import List, Literal
from pydantic import BaseModel as PydanticBaseModel

from fastapi import APIRouter, Depends, Query, BackgroundTasks

from app.core.dependencies import get_current_active_user, get_db
from app.core.exceptions import DuplicatedError
from app.model.user import User
from app.repository.project_member_repository import ProjectMemberRepository
from app.repository.project_repository import ProjectRepository
from app.repository.team_member_repository import TeamMemberRepository
from app.repository.team_repository import TeamRepository
from app.repository.task_status_repository import TaskStatusRepository
from app.repository.task_type_repository import TaskTypeRepository
from app.repository.task_priority_repository import TaskPriorityRepository
from app.repository.task_repository import TaskRepository
from app.repository.task_time_log_repository import TaskTimeLogRepository
from app.schema.base_schema import FindResult, ResponseSchema
from app.schema.project_member_schema import (
    ProjectMemberCreate,
    ProjectMemberRead,
    ProjectMemberUpdate,
    ProjectInviteGenerateRequest,
    ProjectInviteTokenResponse,
    ProjectInviteAcceptRequest,
)
from app.schema.project_schema import (
    ProjectCreate,
    ProjectFind,
    ProjectRead,
    ProjectUpdate,
)
from app.schema.task_schema import (
    ProjectWorkloadResponse,
    TaskRead,
)
from app.services.project_member_service import ProjectMemberService
from app.services.project_permission_service import ProjectPermissionService
from app.services.project_service import ProjectService
from app.services.invitation_service import InvitationService
from app.api.v1.endpoints.invitations import get_invitation_service
from app.services.task_service import TaskService
from app.services.velocity_service import VelocityService
from app.services.estimation_service import EstimationService
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
    task_repository = TaskRepository(lambda: nullcontext(db))
    return ProjectService(
        project_repository=project_repository,
        team_repository=team_repository,
        team_member_repository=team_member_repository,
        project_member_repository=project_member_repository,
        task_status_repository=task_status_repository,
        task_type_repository=task_type_repository,
        task_priority_repository=task_priority_repository,
        task_repository=task_repository,
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


def get_project_permission_service(db=Depends(get_db)) -> ProjectPermissionService:
    return ProjectPermissionService(
        project_repository=ProjectRepository(lambda: nullcontext(db)),
        project_member_repository=ProjectMemberRepository(lambda: nullcontext(db)),
        team_member_repository=TeamMemberRepository(lambda: nullcontext(db)),
        task_repository=TaskRepository(lambda: nullcontext(db)),
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
    team_id: str | None = Query(None),
    current_user: User = Depends(get_current_active_user),
    service: ProjectService = Depends(get_project_service),
):
    result = service.get_my_projects(current_user.id, team_id=team_id)
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


@router.get(
    "/{project_id}/members",
    response_model=ResponseSchema[FindResult[ProjectMemberRead]],
)
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


@router.patch(
    "/{project_id}/members/{user_id}", response_model=ResponseSchema[ProjectMemberRead]
)
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


@router.post(
    "/{project_id}/invitations/generate",
    response_model=ResponseSchema[ProjectInviteTokenResponse],
)
def generate_project_invitation(
    project_id: str,
    schema: ProjectInviteGenerateRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    project_service: ProjectService = Depends(get_project_service),
    project_member_service: ProjectMemberService = Depends(get_project_member_service),
    invitation_service: InvitationService = Depends(get_invitation_service),
):
    project_member_service.check_permission(project_id, current_user.id, "manager")

    project = project_service.get_project_details(project_id, current_user)

    # Check if user with this email is already a member
    target_user = invitation_service.user_repository.read_by_email(schema.email)
    if target_user and project_member_service.is_user_member(
        project_id, target_user.id
    ):
        raise DuplicatedError(
            detail=f"User with email {schema.email} is already a member of this project."
        )

    invitation = invitation_service.create_and_send_invitation(
        email=schema.email,
        inviter=current_user,
        role=schema.role,
        project_id=project_id,
        team_id=project.team_id,
        target_name=project.name,
        background_tasks=background_tasks,
    )
    return ResponseSchema(
        data=ProjectInviteTokenResponse(token=invitation.id),
        message="Invitation sent successfully",
    )


@router.post("/invitations/accept", response_model=ResponseSchema[ProjectMemberRead])
def accept_project_invitation(
    schema: ProjectInviteAcceptRequest,
    current_user: User = Depends(get_current_active_user),
    service: ProjectMemberService = Depends(get_project_member_service),
):
    result = service.accept_invite_token(schema.token, current_user)
    return ResponseSchema(data=result, message="Successfully joined the project")


@router.get("/{project_id}/gantt", response_model=ResponseSchema[List[TaskRead]])
def get_project_gantt(
    project_id: str,
    current_user: User = Depends(get_current_active_user),
    task_service: TaskService = Depends(get_task_service),
    permission_service: ProjectPermissionService = Depends(
        get_project_permission_service
    ),
):
    permission_service.ensure_project_read(project_id, current_user.id)
    result = task_service.get_gantt_data(project_id)
    return ResponseSchema(data=result)


@router.get(
    "/{project_id}/members/workload",
    response_model=ResponseSchema[ProjectWorkloadResponse],
)
def get_project_member_workload(
    project_id: str,
    period: Literal["weekly", "monthly"] = Query(default="weekly"),
    current_user: User = Depends(get_current_active_user),
    service: ProjectMemberService = Depends(get_project_member_service),
    permission_service: ProjectPermissionService = Depends(
        get_project_permission_service
    ),
):
    """
    Workload của từng member trong project — số task/ngày theo tuần hoặc tháng.
    Dùng cho biểu đồ ProjectWorkload trên Dashboard.
    """
    permission_service.ensure_project_read(project_id, current_user.id)
    result = service.get_project_member_workload(project_id, period)
    return ResponseSchema(
        data=result,
        message="Member workload fetched successfully",
    )


class EstimateTaskRequest(PydanticBaseModel):
    title: str
    description: str | None = None


def get_velocity_service(db=Depends(get_db)) -> VelocityService:
    repo = TaskTimeLogRepository(lambda: nullcontext(db))
    return VelocityService(task_time_log_repository=repo)


def get_estimation_service(db=Depends(get_db)) -> EstimationService:
    repo = TaskRepository(lambda: nullcontext(db))
    return EstimationService(task_repository=repo)


@router.get("/{project_id}/velocity-profile", response_model=ResponseSchema[dict])
def get_project_velocity_profile(
    project_id: str,
    current_user: User = Depends(get_current_active_user),
    service: VelocityService = Depends(get_velocity_service),
    permission_service: ProjectPermissionService = Depends(
        get_project_permission_service
    ),
):
    permission_service.ensure_project_read(project_id, current_user.id)
    result = service.get_project_velocity_profile(project_id)
    return ResponseSchema(
        data=result, message="Project velocity profile fetched successfully"
    )


@router.post("/{project_id}/tasks/estimate", response_model=ResponseSchema[dict])
async def estimate_project_task(
    project_id: str,
    schema: EstimateTaskRequest,
    current_user: User = Depends(get_current_active_user),
    service: EstimationService = Depends(get_estimation_service),
    permission_service: ProjectPermissionService = Depends(
        get_project_permission_service
    ),
):
    permission_service.ensure_project_task_write(project_id, current_user.id)
    result = await service.estimate_task(project_id, schema.title, schema.description)
    return ResponseSchema(data=result, message="Task estimate generated successfully")
