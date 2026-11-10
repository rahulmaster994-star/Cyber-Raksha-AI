"""
backend/app/models/threat_intel.py
Database models for Threat Intelligence Indicators, Feeds, and Unified Risk Assessments.
"""
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, Index
from app.database.base import Base


class ThreatIndicator(Base):
    """
    Stores verified Indicators of Compromise (IoCs) and threat intelligence records.
    Types: URL, DOMAIN, IP, HASH, PATTERN
    Sources: URLhaus, PhishTank, OpenPhish, CERT-In, Internal
    """
    __tablename__ = "threat_indicators"

    id = Column(Integer, primary_key=True, index=True)
    indicator_type = Column(String(50), nullable=False, index=True)  # URL, DOMAIN, IP, HASH, KEYWORD
    indicator_value = Column(String(512), nullable=False, index=True)
    threat_type = Column(String(100), nullable=False)  # PHISHING, MALWARE_DOWNLOAD, C2, DIGITAL_ARREST, VOIP_SCAM
    severity = Column(String(50), default="HIGH", nullable=False)  # LOW, MEDIUM, HIGH, CRITICAL
    confidence_score = Column(Float, default=0.9, nullable=False)  # 0.0 to 1.0
    source_name = Column(String(100), nullable=False, index=True)  # URLHAUS, PHISHTANK, CERT_IN, MANUAL
    source_reference = Column(String(255), nullable=True)  # ID or URL in original source feed
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    first_seen = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    last_seen = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        Index("idx_indicator_type_val", "indicator_type", "indicator_value"),
    )

    def __repr__(self) -> str:
        return f"<ThreatIndicator id={self.id} type={self.indicator_type} val={self.indicator_value[:30]}>"


class ThreatFeedLog(Base):
    """
    Tracks threat intelligence feed updates, timestamps, record counts, and status.
    """
    __tablename__ = "threat_feed_logs"

    id = Column(Integer, primary_key=True, index=True)
    source_name = Column(String(100), nullable=False, index=True)
    feed_url = Column(String(512), nullable=True)
    status = Column(String(50), nullable=False)  # SUCCESS, FAILED, RATE_LIMITED, STALE
    records_added = Column(Integer, default=0)
    records_updated = Column(Integer, default=0)
    duration_seconds = Column(Float, default=0.0)
    error_message = Column(Text, nullable=True)
    fetched_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    def __repr__(self) -> str:
        return f"<ThreatFeedLog id={self.id} source={self.source_name} status={self.status}>"


class UnifiedRiskRecord(Base):
    """
    Logs full cross-module unified risk assessments and correlation evidence.
    """
    __tablename__ = "unified_risk_records"

    id = Column(Integer, primary_key=True, index=True)
    submission_type = Column(String(50), nullable=False)  # URL, MESSAGE, MULTI_MODAL, AUDIO_MESSAGE
    target_summary = Column(String(255), nullable=False)
    overall_risk_level = Column(String(50), nullable=False)  # LOW, MEDIUM, HIGH, CRITICAL
    overall_risk_score = Column(Float, nullable=False)  # 0.0 - 100.0
    threat_category = Column(String(100), nullable=False)
    corroboration_factor = Column(Float, default=1.0)  # Multiplier based on independent module agreement
    modules_involved = Column(String(255), nullable=False)  # JSON or comma-separated list
    intelligence_matches_count = Column(Integer, default=0)
    explanation = Column(Text, nullable=False)
    recommended_action = Column(Text, nullable=False)
    evidence_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    def __repr__(self) -> str:
        return f"<UnifiedRiskRecord id={self.id} risk={self.overall_risk_level} score={self.overall_risk_score}>"

