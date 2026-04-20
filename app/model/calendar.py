from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.model.base_model import BaseModel


class Calendar(BaseModel):
    __tablename__ = "calendar"

    # owner can be User or Team
    owner_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    
    # personal, team
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description: Mapped[str | None] = mapped_column(String(512), nullable=True)
