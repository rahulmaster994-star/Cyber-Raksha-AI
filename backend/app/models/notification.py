"""
backend/app/models/notification.py
Cyber Raksha AI - Notification and Notification Preferences Database Models.
Phase A3: Intelligent Security Notification & Alert Engine.
"""
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Index
from app.database.base import Base


class Notification(Base):
    """
    Stores persistent security alert events, detection notices, and system notifications.
    Supports multi-level severity filtering, categorization, domain tracking, and read state.
    """
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String(100), nullable=True, index=True)
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    notification_type = Column(String(50), default="INFO", nullable=False)  # INFO, WARNING, ALERT, CRITICAL
    severity = Column(String(50), default="LOW", nullable=False, index=True)  # CRITICAL, HIGH, MEDIUM, LOW
    category = Column(String(100), default="SECURITY_ALERT", nullable=False, index=True)  # MALICIOUS_WEBSITE, PHISHING_ATTEMPT, HIGH_RISK_URL, THREAT_INTEL_SYNC, SYSTEM_ALERT
    target_domain = Column(String(255), nullable=True, index=True)
    recommended_action = Column(String(255), nullable=True)
    source_component = Column(String(100), default="CORE_ENGINE", nullable=False)
    metadata_json = Column(Text, nullable=True)
    is_read = Column(Boolean, default=False, nullable=False, index=True)
    recipient_role = Column(String(50), default="analyst", nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    __table_args__ = (
        Index("idx_notif_severity_read", "severity", "is_read"),
        Index("idx_notif_created_read", "created_at", "is_read"),
    )

    def __repr__(self) -> str:
        return f"<Notification id={self.id} title={self.title[:30]} severity={self.severity} read={self.is_read}>"


class NotificationPreference(Base):
    """
    Stores user notification preferences, thresholds, category toggles, and sound settings.
    """
    __tablename__ = "notification_preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(100), default="default_user", unique=True, index=True, nullable=False)
    browser_notifications_enabled = Column(Boolean, default=True, nullable=False)
    min_severity = Column(String(50), default="LOW", nullable=False)  # LOW, MEDIUM, HIGH, CRITICAL
    categories_enabled = Column(
        Text,
        default="MALICIOUS_WEBSITE,PHISHING_ATTEMPT,HIGH_RISK_URL,THREAT_INTEL_SYNC,SYSTEM_ALERT",
        nullable=False
    )
    sound_enabled = Column(Boolean, default=False, nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    def __repr__(self) -> str:
        return f"<NotificationPreference user={self.user_id} min_sev={self.min_severity}>"
