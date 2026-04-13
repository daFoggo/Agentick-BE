from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class SignIn(BaseModel):
    email__eq: EmailStr
    password: str = Field(min_length=6, max_length=128)


class SignUp(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)
    name: str = Field(min_length=1, max_length=255)
    avatar_url: str | None = Field(default=None, max_length=512)


class Payload(BaseModel):
    sub: str
    email: EmailStr
    name: str


class UserInfo(BaseModel):
    id: str
    name: str
    email: EmailStr
    avatar_url: str | None = Field(default=None)
    created_at: datetime | None = Field(default=None)

    model_config = ConfigDict(from_attributes=True)


class SignInResponse(BaseModel):
    access_token: str
    expiration: str
    refresh_token: str
    refresh_expiration: str
    user_info: UserInfo


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    expiration: str
    refresh_token: str
    refresh_expiration: str