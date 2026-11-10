"""
Cyber Raksha AI - Mobile Device Database Model
Phase B1 & B2.1: Native Android Foundation & Device Authentication
"""
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime
from app.database.base import Base


class Device(Base):
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String(64), unique=True, index=True, nullable=False)
    device_name = Column(String(100), nullable=False)
    app_version = Column(String(20), default="1.0.0", nullable=False)
    status = Column(String(20), default="ACTIVE", nullable=False)  # ACTIVE, INACTIVE, REVOKED
    security_posture = Column(String(20), default="PROTECTED", nullable=False)  # PROTECTED, AT_RISK, UNKNOWN
    device_token_hash = Column(String(64), nullable=True, index=True)  # SHA-256 of high-entropy token
    is_revoked = Column(Boolean, default=False, nullable=False)
    registered_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    last_seen_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    protection_modules = Column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<Device id={self.id} device_id={self.device_id} name={self.device_name} status={self.status}>"
