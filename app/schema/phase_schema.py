from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from app.schema.base_schema import FindBase, ModelBaseInfo


class PhaseBase(BaseModel):
    project_id: str
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    order: float = Field(..., ge=0)
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class PhaseCreate(PhaseBase):
    pass


class PhaseUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    order: Optional[float] = Field(None, ge=0)
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class PhaseRead(ModelBaseInfo, PhaseBase):
    model_config = ConfigDict(from_attributes=True)


class PhaseFind(FindBase):
    id__eq: Optional[str] = None
    project_id__eq: Optional[str] = None
    name__ilike: Optional[str] = None
