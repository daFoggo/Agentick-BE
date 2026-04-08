from fastapi import APIRouter, Depends

from app.core.dependencies import get_db
from app.repository.user_repository import UserRepository
from app.schema.base_schema import ResponseSchema
from app.schema.auth_schema import SignIn, SignInResponse, SignUp, UserInfo
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


def get_auth_service(db=Depends(get_db)) -> AuthService:
    user_repository = UserRepository(lambda: db)
    return AuthService(user_repository=user_repository)


@router.post("/sign-up", response_model=ResponseSchema[UserInfo])
def sign_up(payload: SignUp, service: AuthService = Depends(get_auth_service)):
    result = service.sign_up(payload)
    return ResponseSchema(data=result, message="User registered successfully")


@router.post("/sign-in", response_model=ResponseSchema[SignInResponse])
def sign_in(payload: SignIn, service: AuthService = Depends(get_auth_service)):
    result = service.sign_in(payload)
    return ResponseSchema(data=result, message="Login successful")
