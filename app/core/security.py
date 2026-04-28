from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import jwt
from jwt import InvalidTokenError
from pwdlib import PasswordHash

from app.core.config import settings
from app.core.exceptions import AuthError

password_hash = PasswordHash.recommended()
ALGORITHM = "HS256"


def _get_secret_key() -> str:
    if not settings.SECRET_KEY:
        raise AuthError(detail="SECRET_KEY is not configured.")
    return settings.SECRET_KEY


def create_access_token(subject: dict[str, Any], expires_delta: timedelta | None = None) -> tuple[str, str]:
    now = datetime.now(timezone.utc)
    expire = now + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    payload = {
        **subject,
        "iat": int(now.timestamp()),
        "nbf": int(now.timestamp()),
        "exp": int(expire.timestamp()),
        "type": "access",
    }
    encoded_jwt = jwt.encode(payload, _get_secret_key(), algorithm=ALGORITHM)
    expiration_datetime = expire.isoformat()
    return encoded_jwt, expiration_datetime


def create_refresh_token(subject: dict[str, Any], expires_delta: timedelta | None = None) -> tuple[str, str]:
    now = datetime.now(timezone.utc)
    expire = now + (
        expires_delta or timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES)
    )
    payload = {
        **subject,
        "iat": int(now.timestamp()),
        "nbf": int(now.timestamp()),
        "exp": int(expire.timestamp()),
        "type": "refresh",
    }
    encoded_jwt = jwt.encode(payload, _get_secret_key(), algorithm=ALGORITHM)
    expiration_datetime = expire.isoformat()
    return encoded_jwt, expiration_datetime


def create_invite_token(subject: dict[str, Any], expires_delta: timedelta | None = None) -> tuple[str, str]:
    now = datetime.now(timezone.utc)
    expire = now + (expires_delta or timedelta(days=7))
    payload = {
        **subject,
        "iat": int(now.timestamp()),
        "nbf": int(now.timestamp()),
        "exp": int(expire.timestamp()),
        "type": "invite",
    }
    encoded_jwt = jwt.encode(payload, _get_secret_key(), algorithm=ALGORITHM)
    expiration_datetime = expire.isoformat()
    return encoded_jwt, expiration_datetime


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_hash.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return password_hash.hash(password)


def decode_jwt(token: str) -> dict[str, Any]:
    try:
        payload = jwt.decode(token, _get_secret_key(), algorithms=[ALGORITHM])
        return payload if isinstance(payload, dict) else {}
    except InvalidTokenError:
        return {}


class JWTBearer(HTTPBearer):
    def __init__(self, auto_error: bool = True):
        super().__init__(auto_error=auto_error)

    async def __call__(self, request: Request) -> str:
        credentials: HTTPAuthorizationCredentials = await super().__call__(request)
        if credentials:
            if credentials.scheme.lower() != "bearer":
                raise AuthError(detail="Invalid authentication scheme.")
            if not self.verify_jwt(credentials.credentials):
                raise AuthError(detail="Invalid token or expired token.")
            return credentials.credentials
        raise AuthError(detail="Invalid authorization code.")

    def verify_jwt(self, jwt_token: str) -> bool:
        return bool(decode_jwt(jwt_token))
