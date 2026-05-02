from datetime import datetime
from pydantic import BaseModel, ConfigDict
from app.model.notification import NotificationType, NotificationStatus

class NotificationResponse(BaseModel):
    id: str
    user_id: str
    title: str
    content: str | None = None
    type: NotificationType
    status: NotificationStatus
    is_read: bool
    is_bookmarked: bool
    resource_id: str | None = None
    resource_type: str | None = None
    data: dict | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class NotificationStatsResponse(BaseModel):
    active_count: int
    unread_count: int
    bookmarks_count: int
    archive_count: int
