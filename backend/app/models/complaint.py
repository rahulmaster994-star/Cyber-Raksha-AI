"""
Cyber Raksha AI - Citizen Cybercrime Complaint Model
Assisted integration with cybercrime.gov.in and Helpline 1930.
"""
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey
from app.database.base import Base


class CybercrimeComplaint(Base):
    __tablename__ = "cybercrime_complaints"

    id = Column(Integer, primary_key=True, index=True)
    complaint_id = Column(String(64), unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    device_id = Column(String(64), nullable=True, index=True)
    incident_id = Column(Integer, nullable=True)
    complaint_category = Column(String(64), nullable=False)  # BANKING_FRAUD, DIGITAL_ARREST, UPI_FRAUD, KYC_SCAM, PHISHING, IMPERSONATION
    suspect_identifier = Column(String(255), nullable=True)  # Phone number, UPI ID, URL, Telegram handle
    financial_loss_inr = Column(Float, default=0.0, nullable=False)
    description = Column(Text, nullable=False)
    evidence_summary = Column(Text, nullable=True)
    evidence_json = Column(Text, nullable=True)
    official_portal_url = Column(String(255), default="https://cybercrime.gov.in", nullable=False)
    helpline_number = Column(String(10), default="1930", nullable=False)
    status = Column(String(32), default="DRAFT", nullable=False)  # DRAFT, AWAITING_SUBMISSION, OFFICIALLY_SUBMITTED, UNDER_REVIEW, ACTION_TAKEN, CLOSED
    official_ack_number = Column(String(100), nullable=True, index=True)
    official_submission_date = Column(DateTime, nullable=True)
    official_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    def __repr__(self) -> str:
        return f"<CybercrimeComplaint id={self.id} complaint_id={self.complaint_id} status={self.status}>"
