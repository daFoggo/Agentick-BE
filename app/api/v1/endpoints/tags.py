from contextlib import nullcontext
from typing import List

from fastapi import APIRouter, Depends

from app.core.dependencies import get_current_active_user, get_db
from app.model.user import User
from app.repository.tag_repository import TagRepository
from app.schema.base_schema import FindResult, ResponseSchema
from app.schema.tag_schema import TagCreate, TagFind, TagRead, TagUpdate
from app.services.tag_service import TagService

router = APIRouter(prefix="/tags", tags=["tags"])


def get_tag_service(db=Depends(get_db)) -> TagService:
    tag_repository = TagRepository(lambda: nullcontext(db))
    return TagService(repository=tag_repository)


@router.post("", response_model=ResponseSchema[TagRead])
def create_tag(
    schema: TagCreate,
    current_user: User = Depends(get_current_active_user),
    service: TagService = Depends(get_tag_service),
):
    result = service.add(schema)
    return ResponseSchema(data=result, message="Tag created successfully")


@router.get("", response_model=ResponseSchema[FindResult[TagRead]])
def get_tags(
    find_query: TagFind = Depends(),
    current_user: User = Depends(get_current_active_user),
    service: TagService = Depends(get_tag_service),
):
    result = service.get_list(find_query)
    return ResponseSchema(data=result)


@router.get("/{tag_id}", response_model=ResponseSchema[TagRead])
def get_tag(
    tag_id: str,
    current_user: User = Depends(get_current_active_user),
    service: TagService = Depends(get_tag_service),
):
    result = service.get_by_id(tag_id)
    return ResponseSchema(data=result)


@router.patch("/{tag_id}", response_model=ResponseSchema[TagRead])
def update_tag(
    tag_id: str,
    schema: TagUpdate,
    current_user: User = Depends(get_current_active_user),
    service: TagService = Depends(get_tag_service),
):
    result = service.patch(tag_id, schema)
    return ResponseSchema(data=result, message="Tag updated successfully")


@router.delete("/{tag_id}", response_model=ResponseSchema[bool])
def delete_tag(
    tag_id: str,
    current_user: User = Depends(get_current_active_user),
    service: TagService = Depends(get_tag_service),
):
    service.remove_by_id(tag_id)
    return ResponseSchema(data=True, message="Tag deleted successfully")
