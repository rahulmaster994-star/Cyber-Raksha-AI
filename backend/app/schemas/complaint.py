"""
Cyber Raksha AI - Cybercrime Complaint Schemas
Assisted submission to cybercrime.gov.in and Helpline 1930.
"""
from typing import Optional, Any, Dict
from pydantic import BaseModel, Field


class ComplaintDraftRequest(BaseModel):
    complaint_category: str = Field(..., description="e.g. BANKING_FRAUD, DIGITAL_ARREST, UPI_FRAUD, KYC_SCAM, PHISHING")
    suspect_identifier: Optional[str] = Field(None, description="Suspect phone, UPI ID, URL, or Telegram handle")
    financial_loss_inr: float = Field(0.0, ge=0.0)
    description: str = Field(..., min_length=10, description="Chronological summary of incident")
    evidence_summary: Optional[str] = None
    evidence_json: Optional[str] = None
    device_id: Optional[str] = None
    incident_id: Optional[int] = None


class RecordAcknowledgementRequest(BaseModel):
    official_ack_number: str = Field(..., min_length=4, max_length=100, description="Citizen acknowledgement number from cybercrime.gov.in or 1930")
    notes: Optional[str] = None


class ComplaintStatusUpdateRequest(BaseModel):
    status: str = Field(..., description="DRAFT, AWAITING_SUBMISSION, OFFICIALLY_SUBMITTED, UNDER_REVIEW, ACTION_TAKEN, CLOSED")
    notes: Optional[str] = None


class ComplaintResponse(BaseModel):
    complaint_id: str
    user_id: Optional[int] = None
    device_id: Optional[str] = None
    complaint_category: str
    suspect_identifier: Optional[str] = None
    financial_loss_inr: float
    description: str
    evidence_summary: Optional[str] = None
    official_portal_url: str
    helpline_number: str
    status: str
    verification_level: str = "USER_REPORTED_UNVERIFIED"
    is_government_verified: bool = False
    official_ack_number: Optional[str] = None
    official_submission_date: Optional[str] = None
    official_notes: Optional[str] = None
    created_at: str
    tracking_instructions: str

