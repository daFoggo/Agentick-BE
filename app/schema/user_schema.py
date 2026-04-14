from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.schema.base_schema import FindBase, ModelBaseInfo


class UserBase(BaseModel):
    email: EmailStr
    name: str = Field(min_length=1, max_length=255)
    avatar_url: str | None = Field(default=None, max_length=512)


class UserCreate(UserBase):
    password: str = Field(min_length=6, max_length=128)


class UserCreateDB(UserBase):
    hashed_password: str
    is_active: bool = True
    is_superuser: bool = False
    user_token: str


class UserUpdate(BaseModel):
    email: EmailStr | None = None
    name: str | None = Field(default=None, min_length=1, max_length=255)
    avatar_url: str | None = Field(default=None, max_length=512)
    password: str | None = Field(default=None, min_length=6, max_length=128)


class UserRead(ModelBaseInfo, UserBase):
    is_active: bool = True

    model_config = ConfigDict(from_attributes=True)


class UserFind(FindBase):
    id__eq: str | None = None
    email__eq: EmailStr | None = None
    name__ilike: str | None = None
    is_active__eq: bool | None = None


class UserSearch(BaseModel):
    """Query params cho search user — dùng cho flow invite member"""
    q: str = Field(min_length=1, max_length=100, description="Search by email or name")
    limit: int = Field(default=10, ge=1, le=50, description="Max results returned")
    team_id: str | None = Field(default=None, description="Exclude members already in this team")


class UserSearchResult(BaseModel):
    """Kết quả search — chỉ trả info cần thiết, KHÔNG trả sensitive data"""
    id: str
    name: str
    email: EmailStr
    avatar_url: str | None = None

    model_config = ConfigDict(from_attributes=True)