"""
backend/app/models/incident.py
Database models for Security Incidents, Incident Actions,
and User Protection Settings.
Phase B3: Unified Protection Integration
"""
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from app.database.base import Base


class SecurityIncident(Base):
    """
    Tracks lifecycle of unified security incidents correlated across Browser, Android,
    and Central Threat Intelligence feeds.
    Statuses:
      - NEW
      - INVESTIGATING
      - ACTION_REQUIRED
      - CONFIRMED
      - CONTAINMENT_IN_PROGRESS
      - RESOLVED
      - CLOSED
      - FALSE_POSITIVE
    """
    __tablename__ = "security_incidents"

    id = Column(Integer, primary_key=True, index=True)
    incident_number = Column(String(50), unique=True, nullable=False, index=True)  # e.g., CR-INC-2026-0001
    category = Column(String(100), nullable=False, index=True)  # PHISHING, FINANCIAL_FRAUD, DIGITAL_ARREST, VOICE_CLONING, ACCOUNT_COMPROMISE, SUSPICIOUS_COMMUNICATION, MALICIOUS_WEBSITE, TELEPHONY_FRAUD
    title = Column(String(255), nullable=False)
    severity = Column(String(50), default="HIGH", nullable=False)  # LOW, MEDIUM, HIGH, CRITICAL
    status = Column(String(50), default="NEW", nullable=False, index=True)
    summary = Column(Text, nullable=False)
    target_or_indicator = Column(String(255), nullable=True, index=True)  # Primary indicator (URL, domain, phone)
    source_components = Column(Text, nullable=True)  # JSON-encoded list, e.g. ["BROWSER_EXTENSION", "THREAT_INTEL_FEED"]
    device_id = Column(String(64), nullable=True, index=True)
    related_analysis_id = Column(Integer, nullable=True)  # Links to AnalysisHistory or UnifiedRiskRecord
    evidence_references = Column(Text, nullable=True)  # JSON string of IOCs / reasons / metadata
    user_acknowledged = Column(Boolean, default=False, nullable=False)
    acknowledged_at = Column(DateTime, nullable=True)
    is_false_positive = Column(Boolean, default=False, nullable=False)
    resolution_notes = Column(Text, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    actions = relationship("IncidentAction", back_populates="incident", cascade="all, delete-orphan")
    events = relationship("SecurityEvent", backref="incident", lazy="select")

    def __repr__(self) -> str:
        return f"<SecurityIncident {self.incident_number} status={self.status} sev={self.severity}>"


class IncidentAction(Base):
    """
    Guided recovery and protection actions assigned to a specific incident.
    Tracks user confirmation and completion status.
    """
    __tablename__ = "incident_actions"

    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(Integer, ForeignKey("security_incidents.id", ondelete="CASCADE"), nullable=False, index=True)
    action_key = Column(String(100), nullable=False)  # e.g., CALL_BANK_1930, ENABLE_MFA, REPORT_PORTAL
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    priority = Column(String(50), default="IMMEDIATE", nullable=False)  # IMMEDIATE, SHORT_TERM, LONG_TERM
    is_completed = Column(Boolean, default=False, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    incident = relationship("SecurityIncident", back_populates="actions")

    def __repr__(self) -> str:
        return f"<IncidentAction id={self.id} key={self.action_key} completed={self.is_completed}>"


class UserProtectionSetting(Base):
    """
    Stores user security alert and privacy preferences.
    """
    __tablename__ = "user_protection_settings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(100), default="default_analyst", unique=True, nullable=False)
    email_alerts_enabled = Column(Boolean, default=False, nullable=False)
    sms_alerts_enabled = Column(Boolean, default=False, nullable=False)
    data_retention_days = Column(Integer, default=90, nullable=False)
    strict_privacy_mode = Column(Boolean, default=True, nullable=False)
    auto_incident_creation = Column(Boolean, default=True, nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    def __repr__(self) -> str:
        return f"<UserProtectionSetting user={self.user_id}>"
