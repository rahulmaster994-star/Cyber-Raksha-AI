"""
Cyber Raksha AI - Administrator Audit Log Database Model
Stage 9/10: Private Admin Security Operations Center (SOC)
Tracks all administrative actions performed in the Private SOC Control Room.
"""
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime
from app.database.base import Base


class AdminAuditLog(Base):
    __tablename__ = "admin_audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    admin_identifier = Column(String(100), nullable=False, index=True)
    action = Column(String(100), nullable=False, index=True)  # e.g., DEVICE_REVOKED, USER_DEACTIVATED, INCIDENT_UPDATED, FLAG_CHANGED
    target_type = Column(String(50), nullable=False, index=True)  # DEVICE, USER, INCIDENT, SYSTEM, IOC, FEEDBACK
    target_id = Column(String(100), nullable=True, index=True)
    details = Column(Text, nullable=True)  # JSON or text description
    ip_address = Column(String(45), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    def __repr__(self) -> str:
        return f"<AdminAuditLog id={self.id} action={self.action} admin={self.admin_identifier}>"
