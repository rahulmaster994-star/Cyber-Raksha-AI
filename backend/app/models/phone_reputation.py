"""
Cyber Raksha AI - Phone Reputation Model
Phase B2 & B2.1: Intelligent SMS & Call Fraud Protection & Security Hardening
"""
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, Index
from app.database.base import Base


class PhoneReputation(Base):
    """
    Stores phone number fraud intelligence and community reputation records.
    Phone numbers are normalized to digits / E.164 format.
    Includes safeguards against Sybil attacks, coordinated false reports,
    false-positive disputes, and temporal reputation decay.
    """
    __tablename__ = "phone_reputations"

    id = Column(Integer, primary_key=True, index=True)
    phone_number = Column(String(50), unique=True, index=True, nullable=False)
    risk_level = Column(String(20), default="UNKNOWN", nullable=False, index=True)  # CRITICAL, HIGH, MEDIUM, LOW, SAFE, UNKNOWN
    fraud_category = Column(String(50), nullable=True)  # DIGITAL_ARREST, BANKING_FRAUD, UPI_SCAM, LOTTERY_SCAM, TELEMARKETING, IMPERSONATION
    report_count = Column(Integer, default=1, nullable=False)
    confidence_score = Column(Float, default=0.5, nullable=False)
    source = Column(String(50), default="COMMUNITY", nullable=False)  # GOV_DATABASE, TRAI_REGISTRY, COMMUNITY, INTERNAL, VERIFIED_THREAT_INTEL
    notes = Column(Text, nullable=True)
    distinct_reporting_devices = Column(Text, nullable=True)  # JSON-encoded set of reporter device hashes
    is_verified_authority = Column(Boolean, default=False, nullable=False)  # True only if corroborated by authoritative intelligence
    classification_reason = Column(Text, nullable=True)  # Explicit rationale for risk level
    dispute_count = Column(Integer, default=0, nullable=False)  # User false-positive flags
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    last_reported_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    last_decay_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        Index("idx_phone_num_risk", "phone_number", "risk_level"),
    )

    def __repr__(self) -> str:
        return f"<PhoneReputation id={self.id} number={self.phone_number} risk={self.risk_level} auth={self.is_verified_authority}>"
