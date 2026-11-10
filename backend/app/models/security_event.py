"""
Cyber Raksha AI - Unified Security Event Database Model
Phase B3: Unified Protection Integration
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Float, ForeignKey
from app.database.base import Base


class SecurityEvent(Base):
    __tablename__ = "security_events"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(String(64), unique=True, index=True, default=lambda: str(uuid.uuid4()))
    event_type = Column(String(100), index=True, nullable=False)  # BROWSER_BLOCKED_URL, SMS_FRAUD_DETECTED, CALL_FRAUD_DETECTED, THREAT_INTEL_MATCH, DEVICE_EVENT, AUTH_EVENT
    severity = Column(String(50), default="INFO", nullable=False)  # INFO, LOW, MEDIUM, HIGH, CRITICAL, SAFE
    source_component = Column(String(100), nullable=False)        # BROWSER_EXTENSION, ANDROID_APP, THREAT_INTEL_FEED, CENTRAL_RISK_ENGINE
    device_id = Column(String(64), nullable=True, index=True)
    threat_indicator = Column(String(255), nullable=True, index=True)  # URL, domain, phone number, hash
    risk_score = Column(Float, default=0.0, nullable=False)
    detection_reason = Column(Text, nullable=True)
    source_ip = Column(String(45), nullable=True)
    description = Column(Text, nullable=False)
    raw_payload = Column(Text, nullable=True)
    is_resolved = Column(Boolean, default=False, nullable=False)
    verification_status = Column(String(50), default="UNVERIFIED", nullable=False)  # UNVERIFIED, CORROBORATED, CONFIRMED_MALICIOUS, FALSE_POSITIVE
    incident_id = Column(Integer, ForeignKey("security_incidents.id", ondelete="SET NULL"), nullable=True, index=True)
    processing_status = Column(String(50), default="PROCESSED", nullable=False)    # PENDING, PROCESSED, CORRELATED, SUPPRESSED
    event_hash = Column(String(64), nullable=True, index=True)                    # Deduplication hash
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    def __repr__(self) -> str:
        return f"<SecurityEvent id={self.id} event_id={self.event_id} type={self.event_type} severity={self.severity}>"
