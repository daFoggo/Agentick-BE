from contextlib import nullcontext
from typing import List

from fastapi import APIRouter, Depends

from app.core.dependencies import get_current_active_user, get_db
from app.model.user import User
from app.repository.project_member_repository import ProjectMemberRepository
from app.repository.project_repository import ProjectRepository
from app.repository.team_member_repository import TeamMemberRepository
from app.repository.team_repository import TeamRepository
from app.schema.base_schema import FindResult, ResponseSchema
from app.schema.project_member_schema import ProjectMemberCreate, ProjectMemberRead, ProjectMemberUpdate
from app.schema.project_schema import ProjectCreate, ProjectFind, ProjectRead, ProjectUpdate
from app.services.project_member_service import ProjectMemberService
from app.services.project_service import ProjectService

router = APIRouter(prefix="/projects", tags=["projects"])


def get_project_service(db=Depends(get_db)) -> ProjectService:
    project_repository = ProjectRepository(lambda: nullcontext(db))
    project_member_repository = ProjectMemberRepository(lambda: nullcontext(db))
    team_repository = TeamRepository(lambda: nullcontext(db))
    team_member_repository = TeamMemberRepository(lambda: nullcontext(db))
    return ProjectService(
        project_repository=project_repository,
        team_repository=team_repository,
        team_member_repository=team_member_repository,
        project_member_repository=project_member_repository,
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
