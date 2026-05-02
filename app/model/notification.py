from sqlalchemy import Column, String, Boolean, ForeignKey, Enum, JSON
from sqlalchemy.orm import relationship, Mapped, mapped_column
from app.model.base_model import BaseModel
import enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.model.user import User

class NotificationType(str, enum.Enum):
    SYSTEM = "SYSTEM"
    INVITATION = "INVITATION"
    TASK_ASSIGNED = "TASK_ASSIGNED"
    PROJECT_UPDATE = "PROJECT_UPDATE"

class NotificationStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"
    BOOKMARKED = "BOOKMARKED"
    DELETED = "DELETED"

class Notification(BaseModel):
    __tablename__ = "notification"

    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("user.id"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    type: Mapped[NotificationType] = mapped_column(Enum(NotificationType), default=NotificationType.SYSTEM, nullable=False)
    status: Mapped[NotificationStatus] = mapped_column(Enum(NotificationStatus), default=NotificationStatus.ACTIVE, nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_bookmarked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Dùng để lưu link hoặc id của tài nguyên liên quan (ví dụ invitation_id)
    resource_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    resource_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    
    # Metadata bổ sung nếu cần
    data: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    user: Mapped["User"] = relationship("User", back_populates="notifications")
