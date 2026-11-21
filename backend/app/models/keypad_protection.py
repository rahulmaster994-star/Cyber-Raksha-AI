"""
Cyber Raksha AI - Keypad User Protection Models
Extends Cyber Raksha AI to protect elderly family members who use traditional keypad/feature phones
(Nokia 105, itel Magic, Samsung Guru, Lava Hero, Jio Bharat, etc.) through their smartphone guardian.
"""
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Float, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.database.base import Base


class KeypadElderlyUser(Base):
    """
    Represents an elderly family member using a traditional keypad/feature phone,
    registered and protected by an authenticated guardian.
    """
    __tablename__ = "keypad_elderly_users"

    id = Column(Integer, primary_key=True, index=True)
    guardian_user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    full_name = Column(String(255), nullable=False)
    mobile_number = Column(String(30), nullable=False, index=True)  # Normalized E.164 (e.g., +919876543210)
    relationship_type = Column("relationship", String(50), nullable=False)  # Father, Mother, Grandfather, etc.
    device_type = Column(String(100), default="Traditional Keypad Phone", nullable=False)  # e.g., Nokia 105, Jio Bharat
    preferred_language = Column(String(10), default="en", nullable=False)  # en, hi, kn
    consent_given = Column(Boolean, default=True, nullable=False)
    consent_notes = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    guardian = relationship("User", backref="keypad_dependents")
    incidents = relationship("KeypadIncident", back_populates="elderly_user", cascade="all, delete-orphan")

    @property
    def relationship(self) -> str:
        return self.relationship_type

    @relationship.setter
    def relationship(self, value: str) -> None:
        self.relationship_type = value

    @property
    def masked_mobile_number(self) -> str:
        if not self.mobile_number or len(self.mobile_number) < 6:
            return self.mobile_number or ""
        return self.mobile_number[:3] + "******" + self.mobile_number[-4:]

    def __repr__(self) -> str:
        return f"<KeypadElderlyUser id={self.id} name={self.full_name} guardian={self.guardian_user_id}>"


class KeypadScamReport(Base):
    """
    Scam number intelligence audit records reported by guardians or community.
    Maintains an audit trail and prevents single unverified reports from declaring confirmed status.
    """
    __tablename__ = "keypad_scam_reports"

    id = Column(Integer, primary_key=True, index=True)
    phone_number = Column(String(50), nullable=False, index=True)
    normalized_number = Column(String(50), nullable=False, index=True)
    guardian_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    elderly_user_id = Column(Integer, ForeignKey("keypad_elderly_users.id", ondelete="SET NULL"), nullable=True)
    reported_by_name = Column(String(100), nullable=True)
    fraud_category = Column(String(50), default="UNKNOWN", nullable=False)  # DIGITAL_ARREST, BANK_KYC, ELECTRICITY_BILL, LOTTERY_PRIZE, PENSION_SCHEME, IMPERSONATION
    claimed_caller_identity = Column(String(100), nullable=True)  # e.g., "Fake Electricity Officer"
    evidence_notes = Column(Text, nullable=True)
    source = Column(String(50), default="GUARDIAN_REPORT", nullable=False)
    is_verified_authority = Column(Boolean, default=False, nullable=False)
    verification_status = Column(String(30), default="COMMUNITY_UNVERIFIED", nullable=False)  # COMMUNITY_UNVERIFIED, CORROBORATED, OFFICIAL_AUTHORITY_VERIFIED
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        Index("idx_keypad_scam_num", "normalized_number"),
    )

    def __repr__(self) -> str:
        return f"<KeypadScamReport id={self.id} number={self.normalized_number} status={self.verification_status}>"


class KeypadIncident(Base):
    """
    Records suspicious incidents submitted for or associated with an elderly keypad phone user.
    Powers the Guardian Alert System and maintains incident history.
    """
    __tablename__ = "keypad_incidents"

    id = Column(Integer, primary_key=True, index=True)
    guardian_user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    elderly_user_id = Column(Integer, ForeignKey("keypad_elderly_users.id", ondelete="SET NULL"), nullable=True, index=True)
    incident_type = Column(String(30), nullable=False)  # KEYPAD_SMS_CHECK, KEYPAD_CALL_CHECK, KEYPAD_SCAM_REPORT
    indicator = Column(String(100), nullable=False)  # Caller phone or SMS sender ID
    raw_content = Column(Text, nullable=True)  # SMS text or caller notes
    risk_score = Column(Float, default=0.0, nullable=False)
    severity = Column(String(20), default="LOW", nullable=False)  # SAFE, LOW, MEDIUM, HIGH, CRITICAL
    category = Column(String(50), default="GENERAL_FRAUD", nullable=False)
    explanation = Column(Text, nullable=False)
    recommended_action = Column(Text, nullable=False)
    guardian_notified = Column(Boolean, default=True, nullable=False)
    is_acknowledged = Column(Boolean, default=False, nullable=False)
    acknowledged_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    elderly_user = relationship("KeypadElderlyUser", back_populates="incidents")

    def __repr__(self) -> str:
        return f"<KeypadIncident id={self.id} type={self.incident_type} sev={self.severity} ack={self.is_acknowledged}>"
