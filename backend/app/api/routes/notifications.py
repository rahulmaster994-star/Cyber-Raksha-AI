"""
backend/app/api/routes/notifications.py
FastAPI route endpoints for Phase A3: Intelligent Security Notification & Alert Engine.
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.services.notification_service import notification_service
from app.schemas.notification import (
    NotificationCreate,
    NotificationResponse,
    NotificationListResponse,
    NotificationUnreadCountResponse,
    NotificationPreferenceResponse,
    NotificationPreferenceUpdate
)

router = APIRouter(prefix="/notifications", tags=["Phase A3: Security Notifications & Alerts"])


@router.get(
    "",
    response_model=NotificationListResponse,
    status_code=status.HTTP_200_OK,
    summary="List Security Notifications",
    description="Returns filtered and sorted security notifications with total and unread counts."
)
def list_notifications(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    is_read: Optional[bool] = None,
    severity: Optional[str] = None,
    category: Optional[str] = None,
    device_id: Optional[str] = Query(None, description="Optional device id to scope private notifications"),
    db: Session = Depends(get_db)
):
    return notification_service.list_notifications(
        db=db,
        limit=limit,
        offset=offset,
        is_read=is_read,
        severity=severity,
        category=category,
        device_id=device_id
    )


@router.get(
    "/unread-count",
    response_model=NotificationUnreadCountResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Unread Notification Count",
    description="Returns the total count of unread notifications for badge counters."
)
def get_unread_count(
    device_id: Optional[str] = Query(None, description="Optional device id to scope private notifications"),
    db: Session = Depends(get_db)
):
    count = notification_service.get_unread_count(db, device_id=device_id)
    return NotificationUnreadCountResponse(unread_count=count)


@router.post(
    "",
    response_model=NotificationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create / Ingest Security Notification",
    description="Ingests a verified security alert, performs deduplication, saves to DB, and broadcasts via SSE."
)
def create_notification(
    payload: NotificationCreate,
    db: Session = Depends(get_db)
):
    return notification_service.create_notification(db=db, payload=payload)


@router.patch(
    "/{id}/read",
    response_model=NotificationResponse,
    status_code=status.HTTP_200_OK,
    summary="Mark Notification as Read",
    description="Updates the read status of a specific security notification."
)
def mark_notification_as_read(
    id: int,
    db: Session = Depends(get_db)
):
    notif = notification_service.mark_as_read(db=db, notification_id=id)
    if not notif:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Notification #{id} not found."
        )
    return notif


@router.post(
    "/read-all",
    status_code=status.HTTP_200_OK,
    summary="Mark All Notifications as Read",
    description="Batch updates all unread notifications to read."
)
def mark_all_notifications_as_read(db: Session = Depends(get_db)):
    count = notification_service.mark_all_as_read(db=db)
    return {"status": "SUCCESS", "marked_read_count": count}


@router.delete(
    "/{id}",
    status_code=status.HTTP_200_OK,
    summary="Delete Notification",
    description="Permanently deletes a specific notification by ID."
)
def delete_notification(
    id: int,
    db: Session = Depends(get_db)
):
    deleted = notification_service.delete_notification(db=db, notification_id=id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Notification #{id} not found."
        )
    return {"status": "SUCCESS", "message": f"Notification #{id} deleted."}


@router.delete(
    "",
    status_code=status.HTTP_200_OK,
    summary="Clear All Notifications",
    description="Deletes all notifications from database history."
)
def clear_all_notifications(db: Session = Depends(get_db)):
    count = notification_service.clear_all(db=db)
    return {"status": "SUCCESS", "cleared_count": count}


@router.get(
    "/preferences",
    response_model=NotificationPreferenceResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Notification Preferences",
    description="Returns user notification preferences, thresholds, and category toggles."
)
def get_preferences(
    user_id: str = "default_user",
    db: Session = Depends(get_db)
):
    return notification_service.get_preferences(db=db, user_id=user_id)


@router.put(
    "/preferences",
    response_model=NotificationPreferenceResponse,
    status_code=status.HTTP_200_OK,
    summary="Update Notification Preferences",
    description="Updates user notification preferences and thresholds."
)
def update_preferences(
    update_data: NotificationPreferenceUpdate,
    user_id: str = "default_user",
    db: Session = Depends(get_db)
):
    return notification_service.update_preferences(db=db, update_data=update_data, user_id=user_id)


@router.get(
    "/stream",
    summary="Real-Time Notification Event Stream (Server-Sent Events)",
    description="Establishes an HTTP SSE connection to push real-time notifications to the dashboard without polling."
)
async def stream_notifications():
    return StreamingResponse(
        notification_service.stream_notifications(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

