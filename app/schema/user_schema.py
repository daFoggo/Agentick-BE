from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.schema.base_schema import FindBase, ModelBaseInfo


class UserBase(BaseModel):
    email: EmailStr
    full_name: str | None = Field(default=None, max_length=255)


class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=128)


class UserUpdate(BaseModel):
    email: EmailStr | None = None
    full_name: str | None = Field(default=None, max_length=255)
    password: str | None = Field(default=None, min_length=8, max_length=128)


class UserRead(ModelBaseInfo, UserBase):
    is_active: bool = True

    model_config = ConfigDict(from_attributes=True)


class UserFind(FindBase):
    id__eq: int | None = None
    email__eq: EmailStr | None = None
    full_name__ilike: str | None = None
    is_active__eq: bool | None = None