"""
Cyber Raksha AI - Community Threat Intelligence Report Model
User-driven reporting, Sybil resistance, and reputation tracking.
"""
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime
from app.database.base import Base


class CommunityReport(Base):
    __tablename__ = "community_reports"

    id = Column(Integer, primary_key=True, index=True)
    indicator = Column(String(255), index=True, nullable=False)
    indicator_type = Column(String(32), nullable=False)  # PHONE, URL, UPI, SMS_SENDER, TELEGRAM
    category = Column(String(64), nullable=False)
    description = Column(Text, nullable=True)
    reporter_user_id = Column(Integer, nullable=True, index=True)
    reporter_device_id = Column(String(64), nullable=True, index=True)
    report_count = Column(Integer, default=1, nullable=False)
    distinct_reporters_count = Column(Integer, default=1, nullable=False)
    reporting_identities_json = Column(Text, default="[]", nullable=False)
    consensus_score = Column(Float, default=0.2, nullable=False)
    is_auto_promoted = Column(Boolean, default=False, nullable=False)
    severity = Column(String(32), default="HIGH", nullable=False)
    verified_status = Column(String(32), default="PENDING_REVIEW", nullable=False)  # PENDING_REVIEW, VERIFIED_MALICIOUS, DISMISSED
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    def __repr__(self) -> str:
        return f"<CommunityReport id={self.id} indicator={self.indicator} reports={self.report_count} distinct={self.distinct_reporters_count}>"
