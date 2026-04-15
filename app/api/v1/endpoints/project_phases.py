from contextlib import nullcontext

from fastapi import APIRouter, Depends

from app.core.dependencies import get_current_active_user, get_db
from app.core.exceptions import NotFoundError
from app.model.user import User
from app.repository.phase_repository import PhaseRepository
from app.schema.base_schema import FindResult, ResponseSchema
from app.schema.phase_schema import PhaseCreate, PhaseFind, PhaseRead, PhaseUpdate
from app.services.phase_service import PhaseService

router = APIRouter(prefix="/projects/{project_id}/phases", tags=["project-phases"])


def get_phase_service(db=Depends(get_db)) -> PhaseService:
    return PhaseService(repository=PhaseRepository(lambda: nullcontext(db)))


def _ensure_phase_in_project(phase: PhaseRead, project_id: str):
    if phase.project_id != project_id:
        raise NotFoundError(detail="Phase not found.")


@router.post("", response_model=ResponseSchema[PhaseRead])
def create_project_phase(
    project_id: str,
    schema: PhaseCreate,
    current_user: User = Depends(get_current_active_user),
    service: PhaseService = Depends(get_phase_service),
):
    scoped_schema = schema.model_copy(update={"project_id": project_id})
    result = service.add(scoped_schema)
    return ResponseSchema(data=result, message="Phase created successfully")


@router.get("", response_model=ResponseSchema[FindResult[PhaseRead]])
def get_project_phases(
    project_id: str,
    find_query: PhaseFind = Depends(),
    current_user: User = Depends(get_current_active_user),
    service: PhaseService = Depends(get_phase_service),
):
    scoped_find = find_query.model_copy(update={"project_id__eq": project_id})
    result = service.get_list(scoped_find)
    return ResponseSchema(data=result)


@router.get("/{phase_id}", response_model=ResponseSchema[PhaseRead])
def get_project_phase(
    project_id: str,
    phase_id: str,
    current_user: User = Depends(get_current_active_user),
    service: PhaseService = Depends(get_phase_service),
):
    result = service.get_by_id(phase_id)
    _ensure_phase_in_project(result, project_id)
    return ResponseSchema(data=result)


@router.patch("/{phase_id}", response_model=ResponseSchema[PhaseRead])
def update_project_phase(
    project_id: str,
    phase_id: str,
    schema: PhaseUpdate,
    current_user: User = Depends(get_current_active_user),
    service: PhaseService = Depends(get_phase_service),
):
    phase = service.get_by_id(phase_id)
    _ensure_phase_in_project(phase, project_id)
    result = service.patch(phase_id, schema)
    return ResponseSchema(data=result, message="Phase updated successfully")


@router.delete("/{phase_id}", response_model=ResponseSchema[bool])
def delete_project_phase(
    project_id: str,
    phase_id: str,
    current_user: User = Depends(get_current_active_user),
    service: PhaseService = Depends(get_phase_service),
):
    phase = service.get_by_id(phase_id)
    _ensure_phase_in_project(phase, project_id)
    service.remove_by_id(phase_id)
    return ResponseSchema(data=True, message="Phase deleted successfully")
