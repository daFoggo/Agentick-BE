from contextlib import nullcontext
from typing import List

from fastapi import APIRouter, Depends

from app.core.dependencies import get_current_active_user, get_db
from app.model.user import User
from app.repository.phase_repository import PhaseRepository
from app.schema.base_schema import FindResult, ResponseSchema
from app.schema.phase_schema import PhaseCreate, PhaseFind, PhaseRead, PhaseUpdate
from app.services.phase_service import PhaseService

router = APIRouter(prefix="/phases", tags=["phases"])


def get_phase_service(db=Depends(get_db)) -> PhaseService:
    phase_repository = PhaseRepository(lambda: nullcontext(db))
    return PhaseService(repository=phase_repository)


@router.post("", response_model=ResponseSchema[PhaseRead])
def create_phase(
    schema: PhaseCreate,
    current_user: User = Depends(get_current_active_user),
    service: PhaseService = Depends(get_phase_service),
):
    result = service.add(schema)
    return ResponseSchema(data=result, message="Phase created successfully")


@router.get("", response_model=ResponseSchema[FindResult[PhaseRead]])
def get_phases(
    find_query: PhaseFind = Depends(),
    current_user: User = Depends(get_current_active_user),
    service: PhaseService = Depends(get_phase_service),
):
    result = service.get_list(find_query)
    return ResponseSchema(data=result)


@router.get("/{phase_id}", response_model=ResponseSchema[PhaseRead])
def get_phase(
    phase_id: str,
    current_user: User = Depends(get_current_active_user),
    service: PhaseService = Depends(get_phase_service),
):
    result = service.get_by_id(phase_id)
    return ResponseSchema(data=result)


@router.patch("/{phase_id}", response_model=ResponseSchema[PhaseRead])
def update_phase(
    phase_id: str,
    schema: PhaseUpdate,
    current_user: User = Depends(get_current_active_user),
    service: PhaseService = Depends(get_phase_service),
):
    result = service.patch(phase_id, schema)
    return ResponseSchema(data=result, message="Phase updated successfully")


@router.delete("/{phase_id}", response_model=ResponseSchema[bool])
def delete_phase(
    phase_id: str,
    current_user: User = Depends(get_current_active_user),
    service: PhaseService = Depends(get_phase_service),
):
    service.remove_by_id(phase_id)
    return ResponseSchema(data=True, message="Phase deleted successfully")
