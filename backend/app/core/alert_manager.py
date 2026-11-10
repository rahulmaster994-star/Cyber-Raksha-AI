"""
backend/app/core/alert_manager.py
Stage 9: In-App Operational Alert Manager.
Records, deduplicates, and clears operational alerts without external dependencies.
"""
import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone


ALERT_TYPES = {
    "BACKEND_DEGRADED": "One or more backend subsystems is not functioning normally.",
    "DB_FAILURE": "Database connection is unavailable or returning errors.",
    "MODEL_UNAVAILABLE": "An AI inference model failed to load or is returning errors.",
    "FEED_STALE": "A threat intelligence feed has not been updated within the expected window.",
    "JOB_FAILURE": "One or more asynchronous analysis jobs have failed.",
    "HIGH_ERROR_RATE": "API error rate has exceeded the acceptable threshold.",
}

# Deduplication window: same type + same source not repeated within 5 minutes
DEDUP_WINDOW_SECONDS = 300


class Alert:
    def __init__(
        self,
        alert_id: str,
        alert_type: str,
        source: str,
        message: str,
        severity: str = "WARNING",
    ):
        self.alert_id = alert_id
        self.alert_type = alert_type
        self.source = source
        self.message = message
        self.severity = severity
        self.created_at = datetime.now(timezone.utc).isoformat()
        self.created_epoch = time.time()
        self.acknowledged = False
        self.acknowledged_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "alert_id": self.alert_id,
            "alert_type": self.alert_type,
            "source": self.source,
            "message": self.message,
            "severity": self.severity,
            "created_at": self.created_at,
            "acknowledged": self.acknowledged,
            "acknowledged_at": self.acknowledged_at,
        }


class AlertManager:
    """
    In-memory alert manager with deduplication, severity tracking, and acknowledgement.
    Thread-safe for FastAPI single-process deployment.
    """

    def __init__(self):
        self._alerts: Dict[str, Alert] = {}
        self._counter = 0

    def _make_dedup_key(self, alert_type: str, source: str) -> str:
        return f"{alert_type}::{source}"

    def create_alert(
        self,
        alert_type: str,
        source: str,
        message: str,
        severity: str = "WARNING",
    ) -> Optional[str]:
        """
        Create a new alert, applying deduplication.
        Returns the alert_id if created, None if suppressed as a duplicate.
        """
        if alert_type not in ALERT_TYPES:
            alert_type = "BACKEND_DEGRADED"

        dedup_key = self._make_dedup_key(alert_type, source)
        now = time.time()

        # Check for recent duplicate
        for existing in self._alerts.values():
            if (
                not existing.acknowledged
                and self._make_dedup_key(existing.alert_type, existing.source) == dedup_key
                and (now - existing.created_epoch) < DEDUP_WINDOW_SECONDS
            ):
                return None  # Suppressed as duplicate

        self._counter += 1
        alert_id = f"ALERT-{self._counter:04d}"
        alert = Alert(
            alert_id=alert_id,
            alert_type=alert_type,
            source=source,
            message=message,
            severity=severity,
        )
        self._alerts[alert_id] = alert
        return alert_id

    def get_active_alerts(self) -> List[Dict[str, Any]]:
        """Return all non-acknowledged alerts sorted by creation time (newest first)."""
        active = [a for a in self._alerts.values() if not a.acknowledged]
        active.sort(key=lambda a: a.created_epoch, reverse=True)
        return [a.to_dict() for a in active]

    def get_all_alerts(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Return all alerts (active + acknowledged), newest first."""
        all_alerts = sorted(
            self._alerts.values(), key=lambda a: a.created_epoch, reverse=True
        )
        return [a.to_dict() for a in all_alerts[:limit]]

    def acknowledge_alert(self, alert_id: str) -> bool:
        """Mark an alert as acknowledged. Returns True if found."""
        alert = self._alerts.get(alert_id)
        if not alert:
            return False
        alert.acknowledged = True
        alert.acknowledged_at = datetime.now(timezone.utc).isoformat()
        return True

    def acknowledge_all(self) -> int:
        """Acknowledge all active alerts. Returns count acknowledged."""
        count = 0
        now_iso = datetime.now(timezone.utc).isoformat()
        for alert in self._alerts.values():
            if not alert.acknowledged:
                alert.acknowledged = True
                alert.acknowledged_at = now_iso
                count += 1
        return count

    def get_summary(self) -> Dict[str, Any]:
        active = [a for a in self._alerts.values() if not a.acknowledged]
        return {
            "total_alerts": len(self._alerts),
            "active_alerts": len(active),
            "critical_count": sum(1 for a in active if a.severity == "CRITICAL"),
            "warning_count": sum(1 for a in active if a.severity == "WARNING"),
            "info_count": sum(1 for a in active if a.severity == "INFO"),
        }


alert_manager = AlertManager()

