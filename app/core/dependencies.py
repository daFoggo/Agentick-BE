from functools import lru_cache
from typing import Any, Generator

from fastapi import Depends

from app.core.config import settings
from app.core.database import Database
from app.core.exceptions import AuthError
from app.core.security import JWTBearer, decode_jwt
from app.model.user import User


@lru_cache
def get_database() -> Database:
    return Database(settings.DATABASE_URI)


def get_db() -> Generator:
    with get_database().session() as session:
        yield session


def get_bearer_token(token: str = Depends(JWTBearer())) -> str:
    return token


def get_token_payload(token: str = Depends(get_bearer_token)) -> dict[str, Any]:
    payload = decode_jwt(token)
    if not payload:
        raise AuthError(detail="Invalid token payload.")
    return payload


def get_current_user(payload: dict[str, Any] = Depends(get_token_payload), db=Depends(get_db)) -> User:
    user_id = payload.get("sub")
    if not user_id:
        raise AuthError(detail="Invalid token payload.")

    try:
        user_id = int(user_id)
    except (TypeError, ValueError):
        raise AuthError(detail="Invalid user id in token.")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise AuthError(detail="User not found.")
    return user


def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_active:
        raise AuthError(detail="Inactive user.")
    return current_user


def get_current_super_user(current_user: User = Depends(get_current_active_user)) -> User:
    if not current_user.is_superuser:
        raise AuthError(detail="Insufficient privileges.")
    return current_user
