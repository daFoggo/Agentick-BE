from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class SignIn(BaseModel):
    email__eq: EmailStr
    password: str = Field(min_length=6, max_length=128)


class SignUp(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)
    name: str = Field(min_length=1, max_length=255)
    avatar_url: str | None = Field(default=None, alias="avatarUrl", max_length=512)

    model_config = ConfigDict(populate_by_name=True)


class Payload(BaseModel):
    sub: str
    email: EmailStr
    name: str


class UserInfo(BaseModel):
    id: str
    name: str
    email: EmailStr
    avatar_url: str | None = Field(default=None, alias="avatarUrl")
    created_at: datetime | None = Field(default=None, alias="createdAt")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class SignInResponse(BaseModel):
    access_token: str
    expiration: str
    user_info: UserInfo

    model_config = ConfigDict(populate_by_name=True)