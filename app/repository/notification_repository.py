from contextlib import AbstractContextManager
from typing import Callable
from sqlalchemy.orm import Session
from app.model.notification import Notification, NotificationStatus
from app.repository.base_repository import BaseRepository

class NotificationRepository(BaseRepository):
    def __init__(self, session_factory: Callable[..., AbstractContextManager[Session]]) -> None:
        super().__init__(session_factory, Notification)

    def get_unread_count(self, user_id: str) -> int:
        with self.session_factory() as session:
            return session.query(Notification).filter(
                Notification.user_id == user_id,
                Notification.status == NotificationStatus.ACTIVE
            ).count()

    def get_stats(self, user_id: str) -> dict:
        with self.session_factory() as session:
            # Active (Unread)
            active_count = session.query(Notification).filter(
                Notification.user_id == user_id,
                Notification.status == NotificationStatus.ACTIVE
            ).count()
            
            # Bookmarks (Read but saved)
            bookmarks_count = session.query(Notification).filter(
                Notification.user_id == user_id,
                Notification.status == NotificationStatus.BOOKMARKED
            ).count()
            
            # Archive (Read)
            archive_count = session.query(Notification).filter(
                Notification.user_id == user_id,
                Notification.status == NotificationStatus.ARCHIVED
            ).count()

            return {
                "active_count": active_count,
                "unread_count": active_count,
                "bookmarks_count": bookmarks_count,
                "archive_count": archive_count
            }
