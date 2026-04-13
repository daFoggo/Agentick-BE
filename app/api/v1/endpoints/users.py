from contextlib import nullcontext
from fastapi import APIRouter, Depends

from app.core.dependencies import get_db, get_current_active_user
from app.model.user import User
from app.repository.user_repository import UserRepository
from app.schema.base_schema import ResponseSchema
from app.schema.auth_schema import UserInfo
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["users"])


def get_user_service(db=Depends(get_db)) -> UserService:
    user_repository = UserRepository(lambda: nullcontext(db))
    return UserService(user_repository=user_repository)


@router.get("/me", response_model=ResponseSchema[UserInfo])
def get_me(user: User = Depends(get_current_active_user), service: UserService = Depends(get_user_service)):
    result = service.get_me(user)
    return ResponseSchema(data=result, message="User profile fetched successfully")
