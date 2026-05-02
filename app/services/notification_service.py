from app.repository.notification_repository import NotificationRepository
from app.model.notification import Notification, NotificationStatus, NotificationType

class NotificationService:
    def __init__(self, notification_repository: NotificationRepository) -> None:
        self.notification_repository = notification_repository

    def get_user_notifications(self, user_id: str, status: NotificationStatus = NotificationStatus.ACTIVE, is_read: bool = None, is_bookmarked: bool = None):
        from app.schema.base_schema import FindBase
        class NotificationFind(FindBase):
            user_id__eq: str = user_id
            status__eq: NotificationStatus = status
            is_read__eq: bool = is_read
            is_bookmarked__eq: bool = is_bookmarked
            ordering: str = "-created_at"
        
        return self.notification_repository.read_by_options(NotificationFind())

    def toggle_bookmark(self, notification_id: str, user_id: str):
        notification = self.notification_repository.read_by_id(notification_id)
        if notification.user_id != user_id:
            from fastapi import HTTPException
            raise HTTPException(status_code=403, detail="Forbidden")
        
        # Nếu đang là BOOKMARKED thì bỏ bookmark (chuyển sang ARCHIVED - đã đọc)
        # Nếu không thì chuyển sang BOOKMARKED (đã đọc nhưng lưu lại)
        new_status = NotificationStatus.ARCHIVED if notification.status == NotificationStatus.BOOKMARKED else NotificationStatus.BOOKMARKED
        return self.notification_repository.update_attr(notification_id, "status", new_status)

    def get_stats(self, user_id: str):
        return self.notification_repository.get_stats(user_id)

    def mark_as_read(self, notification_id: str, user_id: str):
        notification = self.notification_repository.read_by_id(notification_id)
        if notification.user_id != user_id:
            from fastapi import HTTPException
            raise HTTPException(status_code=403, detail="Forbidden")
        
        # Đánh dấu đã đọc = chuyển sang ARCHIVED
        return self.notification_repository.update_attr(notification_id, "status", NotificationStatus.ARCHIVED)

    def archive_notification(self, notification_id: str, user_id: str):
        notification = self.notification_repository.read_by_id(notification_id)
        if notification.user_id != user_id:
            from fastapi import HTTPException
            raise HTTPException(status_code=403, detail="Forbidden")
        
        return self.notification_repository.update_attr(notification_id, "status", NotificationStatus.ARCHIVED)

    def unarchive_notification(self, notification_id: str, user_id: str):
        notification = self.notification_repository.read_by_id(notification_id)
        if notification.user_id != user_id:
            from fastapi import HTTPException
            raise HTTPException(status_code=403, detail="Forbidden")
        
        # Trả về trạng thái ACTIVE (chưa đọc)
        return self.notification_repository.update_attr(notification_id, "status", NotificationStatus.ACTIVE)

    def delete_notification(self, notification_id: str, user_id: str):
        notification = self.notification_repository.read_by_id(notification_id)
        if notification.user_id != user_id:
            from fastapi import HTTPException
            raise HTTPException(status_code=403, detail="Forbidden")
        
        self.notification_repository.delete_by_id(notification_id)
        return True

    def create_notification(
        self, 
        user_id: str, 
        title: str, 
        content: str = None, 
        type: NotificationType = NotificationType.SYSTEM,
        resource_id: str = None,
        resource_type: str = None,
        data: dict = None
    ):
        notification_data = {
            "user_id": user_id,
            "title": title,
            "content": content,
            "type": type,
            "resource_id": resource_id,
            "resource_type": resource_type,
            "data": data,
            "is_read": False,
            "status": NotificationStatus.ACTIVE
        }
        return self.notification_repository.create(notification_data)
