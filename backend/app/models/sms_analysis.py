"""
Cyber Raksha AI - SMS Analysis History Model
Phase B2: Intelligent SMS & Call Fraud Protection
"""
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, Index
from app.database.base import Base


class SmsAnalysis(Base):
    """
    Stores metadata and results of SMS analyses.
    Strict privacy requirement: raw message text is NEVER stored.
    Only the SHA-256 hash of the content is stored for deduplication and audit.
    """
    __tablename__ = "sms_analyses"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String(64), index=True, nullable=False)
    message_hash = Column(String(64), index=True, nullable=False)
    risk_score = Column(Float, nullable=False)  # 0.0 - 100.0
    risk_level = Column(String(20), nullable=False, index=True)  # CRITICAL, HIGH, MEDIUM, LOW, SAFE
    fraud_category = Column(String(50), nullable=False)  # BANKING_FRAUD, UPI_FRAUD, OTP_FRAUD, DELIVERY_SCAM, LOTTERY_SCAM, GOV_IMPERSONATION, BENIGN
    detection_reasons = Column(Text, nullable=False)  # JSON-encoded array of detection strings
    urls_found = Column(Text, nullable=True)  # JSON-encoded array of URLs extracted
    analyzed_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    is_false_positive = Column(Boolean, default=False, nullable=False)

    __table_args__ = (
        Index("idx_sms_device_time", "device_id", "analyzed_at"),
    )

    def __repr__(self) -> str:
        return f"<SmsAnalysis id={self.id} device={self.device_id[:8]} risk={self.risk_level} score={self.risk_score}>"

