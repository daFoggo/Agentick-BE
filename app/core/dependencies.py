from functools import lru_cache
from typing import Any, Generator

from fastapi import Depends

from app.core.config import settings
from app.core.database import Database
from app.core.exceptions import AuthError
from app.core.security import JWTBearer, decode_jwt


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
