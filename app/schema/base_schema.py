from datetime import datetime
from typing import Any, Generic, List, Optional, TypeVar, Union

from pydantic import BaseModel

T = TypeVar("T")


class ModelBaseInfo(BaseModel):
    id: str
    created_at: datetime
    updated_at: datetime


class ResponseSchema(BaseModel, Generic[T]):
    success: bool = True
    message: str = "Success"
    data: Optional[T] = None


class FindBase(BaseModel):
    ordering: Optional[str] = None
    page: Optional[int] = None
    page_size: Optional[Union[int, str]] = None


class SearchOptions(FindBase):
    total_count: Optional[int]


class FindResult(BaseModel, Generic[T]):
    founds: Optional[List[T]]
    search_options: Optional[SearchOptions]


class FindDateRange(BaseModel):
    created_at__lt: str
    created_at__lte: str
    created_at__gt: str
    created_at__gte: str


class Blank(BaseModel):
    pass
