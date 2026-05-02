from contextlib import nullcontext
from fastapi import APIRouter, Depends, Query
from typing import List, Optional

from app.core.dependencies import get_db, get_current_active_user
from app.model.user import User
from app.model.notification import NotificationStatus
from app.repository.notification_repository import NotificationRepository
from app.schema.base_schema import ResponseSchema, FindBase
from app.schema.notification_schema import NotificationResponse, NotificationStatsResponse
from app.services.notification_service import NotificationService

router = APIRouter(prefix="/notifications", tags=["notifications"])

def get_notification_service(db=Depends(get_db)) -> NotificationService:
    notification_repository = NotificationRepository(lambda: nullcontext(db))
    return NotificationService(notification_repository=notification_repository)

@router.get("/me", response_model=ResponseSchema[List[NotificationResponse]])
def get_my_notifications(
    status: Optional[NotificationStatus] = Query(NotificationStatus.ACTIVE),
    is_read: Optional[bool] = Query(None),
    is_bookmarked: Optional[bool] = Query(None),
    current_user: User = Depends(get_current_active_user),
    service: NotificationService = Depends(get_notification_service)
):
    notifications = service.get_user_notifications(current_user.id, status, is_read, is_bookmarked)
    return ResponseSchema(data=notifications["founds"], message="Notifications fetched successfully")

@router.patch("/{notification_id}/bookmark", response_model=ResponseSchema[NotificationResponse])
def toggle_bookmark(
    notification_id: str,
    current_user: User = Depends(get_current_active_user),
    service: NotificationService = Depends(get_notification_service)
):
    notification = service.toggle_bookmark(notification_id, current_user.id)
    return ResponseSchema(data=notification, message="Notification bookmark status updated")

@router.get("/stats", response_model=ResponseSchema[NotificationStatsResponse])
def get_notification_stats(
    current_user: User = Depends(get_current_active_user),
    service: NotificationService = Depends(get_notification_service)
):
    stats = service.get_stats(current_user.id)
    return ResponseSchema(data=stats, message="Notification stats fetched successfully")

@router.patch("/{notification_id}/read", response_model=ResponseSchema[NotificationResponse])
def mark_as_read(
    notification_id: str,
    current_user: User = Depends(get_current_active_user),
    service: NotificationService = Depends(get_notification_service)
):
    notification = service.mark_as_read(notification_id, current_user.id)
    return ResponseSchema(data=notification, message="Notification marked as read")

@router.patch("/{notification_id}/archive", response_model=ResponseSchema[NotificationResponse])
def archive_notification(
    notification_id: str,
    current_user: User = Depends(get_current_active_user),
    service: NotificationService = Depends(get_notification_service)
):
    notification = service.archive_notification(notification_id, current_user.id)
    return ResponseSchema(data=notification, message="Notification archived")

@router.patch("/{notification_id}/unarchive", response_model=ResponseSchema[NotificationResponse])
def unarchive_notification(
    notification_id: str,
    current_user: User = Depends(get_current_active_user),
    service: NotificationService = Depends(get_notification_service)
):
    notification = service.unarchive_notification(notification_id, current_user.id)
    return ResponseSchema(data=notification, message="Notification restored from archive")

@router.delete("/{notification_id}", response_model=ResponseSchema[bool])
def delete_notification(
    notification_id: str,
    current_user: User = Depends(get_current_active_user),
    service: NotificationService = Depends(get_notification_service)
):
    service.delete_notification(notification_id, current_user.id)
    return ResponseSchema(data=True, message="Notification deleted")
