"""
backend/app/services/notification_service.py
Service Layer for Phase A3: Intelligent Security Notification & Alert Engine.
Handles event ingestion, multi-level risk categorization, deduplication,
real-time SSE event streaming, database persistence, and user preferences.
"""
import asyncio
import json
import logging
import time
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Set, AsyncGenerator
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_

from app.models.notification import Notification, NotificationPreference
from app.models.security_event import SecurityEvent
from app.schemas.notification import (
    NotificationCreate,
    NotificationResponse,
    NotificationListResponse,
    NotificationPreferenceResponse,
    NotificationPreferenceUpdate
)

logger = logging.getLogger("cyber_raksha.notifications")

VALID_SEVERITIES = {"CRITICAL", "HIGH", "MEDIUM", "LOW"}
SEVERITY_RANKS = {"LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}
VALID_CATEGORIES = {
    "MALICIOUS_WEBSITE",
    "PHISHING_ATTEMPT",
    "HIGH_RISK_URL",
    "THREAT_INTEL_SYNC",
    "SYSTEM_ALERT",
    "SECURITY_ALERT"
}
DEDUPLICATION_WINDOW_SECONDS = 30.0


class NotificationService:
    def __init__(self):
        # In-memory deduplication index: event_key -> (timestamp, severity_rank)
        self._recent_events: Dict[str, tuple[float, int]] = {}
        # Active SSE subscriber tuples: (queue, client_device_id, is_admin)
        self._subscribers: Set[tuple[asyncio.Queue, Optional[str], bool]] = set()

    def _cleanup_recent_events(self, now: float):
        """Prunes deduplication entries older than window."""
        stale_keys = [
            k for k, (ts, _) in self._recent_events.items()
            if now - ts > DEDUPLICATION_WINDOW_SECONDS
        ]
        for k in stale_keys:
            self._recent_events.pop(k, None)

    def is_duplicate_event(self, category: str, target_domain: Optional[str], title: str, severity: str) -> bool:
        """
        Determines if an event is a duplicate within the deduplication window.
        Allows higher severity escalations to break through.
        """
        now = time.time()
        self._cleanup_recent_events(now)

        key_target = (target_domain or title[:50]).strip().lower()
        event_key = f"{category.upper()}:{key_target}"
        incoming_rank = SEVERITY_RANKS.get(severity.upper(), 1)

        if event_key in self._recent_events:
            prev_time, prev_rank = self._recent_events[event_key]
            if now - prev_time <= DEDUPLICATION_WINDOW_SECONDS:
                # If incoming is not higher rank, consider it duplicate
                if incoming_rank <= prev_rank:
                    return True

        self._recent_events[event_key] = (now, incoming_rank)
        return False

    def create_notification(self, db: Session, payload: NotificationCreate) -> NotificationResponse:
        """
        Validates, deduplicates, persists notification, and broadcasts via SSE.
        """
        severity = payload.severity.upper() if payload.severity else "LOW"
        if severity not in VALID_SEVERITIES:
            severity = "MEDIUM"

        category = payload.category.upper() if payload.category else "SECURITY_ALERT"
        if category not in VALID_CATEGORIES:
            category = "SECURITY_ALERT"

        # Check deduplication
        is_dup = self.is_duplicate_event(category, payload.target_domain, payload.title, severity)
        if is_dup:
            logger.info(f"Suppressed duplicate notification: {category} for {payload.target_domain}")
            # Find the existing recent notification to return
            existing = (
                db.query(Notification)
                .filter(Notification.category == category)
                .order_by(desc(Notification.created_at))
                .first()
            )
            if existing:
                return self._to_response(existing)

        # Sanitize text
        clean_title = payload.title.strip()[:200]
        clean_message = payload.message.strip()[:2000]
        clean_domain = payload.target_domain.strip().lower()[:255] if payload.target_domain else None
        clean_action = payload.recommended_action.strip()[:255] if payload.recommended_action else None

        meta_str = json.dumps(payload.metadata_json) if payload.metadata_json else None
        target_dev = payload.device_id or (payload.metadata_json.get("device_id") if payload.metadata_json else None)

        notif = Notification(
            device_id=target_dev,
            title=clean_title,
            message=clean_message,
            notification_type=severity,
            severity=severity,
            category=category,
            target_domain=clean_domain,
            recommended_action=clean_action,
            source_component=payload.source_component[:100],
            metadata_json=meta_str,
            is_read=False,
            recipient_role="analyst",
            created_at=datetime.now(timezone.utc)
        )

        db.add(notif)

        # Also create SecurityEvent for high/critical threats to maintain unified audit log
        if severity in ["CRITICAL", "HIGH"]:
            sec_event = SecurityEvent(
                event_type=f"NOTIF_{category}",
                severity=severity,
                source_component=payload.source_component[:100],
                description=f"{clean_title}: {clean_message[:150]}",
                raw_payload=meta_str,
                created_at=datetime.now(timezone.utc)
            )
            try:
                db.add(sec_event)
            except Exception:
                pass

        db.commit()
        db.refresh(notif)

        response = self._to_response(notif)
        # Broadcast asynchronously to active SSE clients
        self.broadcast_event(response.model_dump())

        return response

    def _to_response(self, notif: Notification) -> NotificationResponse:
        return NotificationResponse(
            id=notif.id,
            device_id=getattr(notif, "device_id", None),
            title=notif.title,
            message=notif.message,
            notification_type=notif.notification_type or notif.severity,
            severity=notif.severity or notif.notification_type or "LOW",
            category=notif.category or "SECURITY_ALERT",
            target_domain=notif.target_domain,
            recommended_action=notif.recommended_action,
            source_component=notif.source_component or "CORE_ENGINE",
            metadata_json=notif.metadata_json,
            is_read=notif.is_read,
            recipient_role=notif.recipient_role or "analyst",
            created_at=notif.created_at.isoformat() if notif.created_at else datetime.now(timezone.utc).isoformat()
        )

    def list_notifications(
        self,
        db: Session,
        limit: int = 50,
        offset: int = 0,
        is_read: Optional[bool] = None,
        severity: Optional[str] = None,
        category: Optional[str] = None,
        device_id: Optional[str] = None
    ) -> NotificationListResponse:
        """Retrieves filtered, sorted notification history with unread count."""
        query = db.query(Notification)

        if device_id:
            query = query.filter(or_(Notification.device_id == device_id, Notification.device_id.is_(None)))

        if is_read is not None:
            query = query.filter(Notification.is_read == is_read)
        if severity:
            query = query.filter(Notification.severity == severity.upper())
        if category:
            query = query.filter(Notification.category == category.upper())

        total = query.count()
        unread_q = db.query(Notification).filter(Notification.is_read == False)
        if device_id:
            unread_q = unread_q.filter(or_(Notification.device_id == device_id, Notification.device_id.is_(None)))
        unread_count = unread_q.count()

        items = (
            query.order_by(desc(Notification.created_at))
            .offset(offset)
            .limit(limit)
            .all()
        )

        return NotificationListResponse(
            total=total,
            unread_count=unread_count,
            items=[self._to_response(item) for item in items]
        )

    def get_unread_count(self, db: Session, device_id: Optional[str] = None) -> int:
        q = db.query(Notification).filter(Notification.is_read == False)
        if device_id:
            q = q.filter(or_(Notification.device_id == device_id, Notification.device_id.is_(None)))
        return q.count()

    def mark_as_read(self, db: Session, notification_id: int) -> Optional[NotificationResponse]:
        notif = db.query(Notification).filter(Notification.id == notification_id).first()
        if not notif:
            return None
        notif.is_read = True
        db.commit()
        db.refresh(notif)
        return self._to_response(notif)

    def mark_all_as_read(self, db: Session) -> int:
        count = db.query(Notification).filter(Notification.is_read == False).update({"is_read": True})
        db.commit()
        return count

    def delete_notification(self, db: Session, notification_id: int) -> bool:
        notif = db.query(Notification).filter(Notification.id == notification_id).first()
        if not notif:
            return False
        db.delete(notif)
        db.commit()
        return True

    def clear_all(self, db: Session) -> int:
        count = db.query(Notification).delete()
        db.commit()
        return count

    def get_preferences(self, db: Session, user_id: str = "default_user") -> NotificationPreferenceResponse:
        pref = db.query(NotificationPreference).filter(NotificationPreference.user_id == user_id).first()
        if not pref:
            pref = NotificationPreference(
                user_id=user_id,
                browser_notifications_enabled=True,
                min_severity="LOW",
                categories_enabled="MALICIOUS_WEBSITE,PHISHING_ATTEMPT,HIGH_RISK_URL,THREAT_INTEL_SYNC,SYSTEM_ALERT",
                sound_enabled=False,
                updated_at=datetime.now(timezone.utc)
            )
            db.add(pref)
            db.commit()
            db.refresh(pref)

        cats = [c.strip() for c in (pref.categories_enabled or "").split(",") if c.strip()]
        return NotificationPreferenceResponse(
            user_id=pref.user_id,
            browser_notifications_enabled=pref.browser_notifications_enabled,
            min_severity=pref.min_severity,
            categories_enabled=cats,
            sound_enabled=pref.sound_enabled,
            updated_at=pref.updated_at.isoformat() if pref.updated_at else datetime.now(timezone.utc).isoformat()
        )

    def update_preferences(
        self,
        db: Session,
        update_data: NotificationPreferenceUpdate,
        user_id: str = "default_user"
    ) -> NotificationPreferenceResponse:
        pref = db.query(NotificationPreference).filter(NotificationPreference.user_id == user_id).first()
        if not pref:
            pref = NotificationPreference(user_id=user_id)
            db.add(pref)

        if update_data.browser_notifications_enabled is not None:
            pref.browser_notifications_enabled = update_data.browser_notifications_enabled

        if update_data.min_severity is not None:
            sev = update_data.min_severity.upper()
            if sev in VALID_SEVERITIES:
                pref.min_severity = sev

        if update_data.categories_enabled is not None:
            valid_cats = [c.upper() for c in update_data.categories_enabled if c.upper() in VALID_CATEGORIES]
            pref.categories_enabled = ",".join(valid_cats)

        if update_data.sound_enabled is not None:
            pref.sound_enabled = update_data.sound_enabled

        pref.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(pref)

        cats = [c.strip() for c in (pref.categories_enabled or "").split(",") if c.strip()]
        return NotificationPreferenceResponse(
            user_id=pref.user_id,
            browser_notifications_enabled=pref.browser_notifications_enabled,
            min_severity=pref.min_severity,
            categories_enabled=cats,
            sound_enabled=pref.sound_enabled,
            updated_at=pref.updated_at.isoformat()
        )

    # ---------------------------------------------------------------------------
    # Real-Time SSE Broadcasting with Multi-Device Scoping (Phase B3.1)
    # ---------------------------------------------------------------------------
    def broadcast_event(self, event_data: Dict[str, Any]):
        """
        Pushes event data to permitted subscriber queues according to authorization scope.
        Device-specific alerts are NEVER broadcast to other devices.
        """
        # Determine target device id
        meta = event_data.get("metadata_json") or {}
        if isinstance(meta, str):
            try:
                meta = json.loads(meta)
            except Exception:
                meta = {}
        target_device = event_data.get("device_id") or meta.get("device_id")

        msg = json.dumps(event_data)
        for (queue, client_dev, is_admin) in list(self._subscribers):
            # If event is private to a device:
            if target_device:
                if not (is_admin or client_dev == target_device):
                    # Strict isolation: Do NOT leak to another device!
                    continue
            try:
                queue.put_nowait(msg)
            except asyncio.QueueFull:
                # Handle slow clients: discard oldest item to prevent memory exhaustion
                try:
                    queue.get_nowait()
                    queue.put_nowait(msg)
                except Exception:
                    pass
            except Exception:
                pass

    async def stream_notifications(
        self,
        client_device_id: Optional[str] = None,
        is_admin: bool = False
    ) -> AsyncGenerator[str, None]:
        """
        Async generator yielding SSE data messages to authorized clients.
        Bounded queue (maxsize=100) prevents slow clients from exhausting server memory.
        """
        queue: asyncio.Queue = asyncio.Queue(maxsize=100)
        sub_entry = (queue, client_device_id, is_admin)
        self._subscribers.add(sub_entry)
        scope_label = "ADMIN" if is_admin else (f"DEVICE:{client_device_id}" if client_device_id else "GLOBAL")
        try:
            # Yield initial connection confirmation with authorized scope
            yield f"event: connected\ndata: {json.dumps({'status': 'CONNECTED', 'scope': scope_label, 'timestamp': datetime.now(timezone.utc).isoformat()})}\n\n"
            while True:
                data = await queue.get()
                yield f"event: notification\ndata: {data}\n\n"
        except asyncio.CancelledError:
            pass
        finally:
            self._subscribers.discard(sub_entry)


# Singleton service instance
notification_service = NotificationService()

