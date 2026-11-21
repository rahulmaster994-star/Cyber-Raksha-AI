"""
Cyber Raksha AI - Keypad User Protection Pydantic Schemas
"""
import re
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict, field_validator


# ── Family Registration Schemas ──────────────────────────────────────────────

class KeypadElderlyUserCreate(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=255, description="Full name of elderly family member")
    mobile_number: str = Field(..., min_length=10, max_length=20, description="Mobile number e.g. 9876543210 or +919876543210")
    relationship: str = Field(default="Parent", max_length=50, description="Relationship to guardian: Father, Mother, Grandfather, Grandmother, Uncle, Aunt, Other")
    device_type: str = Field(default="Nokia 105", max_length=100, description="Model of keypad phone (e.g. Nokia 105, itel Magic, Jio Bharat, Samsung Guru, Lava Hero)")
    preferred_language: str = Field(default="en", description="Preferred language for alerts and guides: en, hi, kn")
    consent_given: bool = Field(default=True, description="Guardian confirmation of elderly family member consent")
    consent_notes: Optional[str] = Field(None, description="Optional notes on consent or caregiver guardianship")

    @field_validator("consent_given")
    @classmethod
    def validate_consent(cls, v: bool) -> bool:
        if not v:
            raise ValueError("Elderly family member consent is required to activate guardian protection shield.")
        return v

    @field_validator("mobile_number")
    @classmethod
    def validate_mobile(cls, v: str) -> str:
        digits = re.sub(r"\D", "", v)
        if len(digits) < 10 or len(digits) > 15:
            raise ValueError("Mobile number must contain between 10 and 15 digits.")
        return v


class KeypadElderlyUserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    guardian_user_id: int
    full_name: str
    mobile_number: str
    masked_mobile_number: str
    relationship: str
    device_type: str
    preferred_language: str
    consent_given: bool
    is_active: bool
    created_at: datetime


# ── SMS Check Schemas ────────────────────────────────────────────────────────

class KeypadSmsCheckRequest(BaseModel):
    elderly_user_id: Optional[int] = Field(None, description="ID of protected elderly member if registered")
    sender: Optional[str] = Field(None, max_length=100, description="SMS sender identifier e.g. +919876501234 or VK-HDFCBK")
    message: str = Field(..., min_length=1, max_length=10000, description="Exact SMS message text received on the keypad phone")
    preferred_language: Optional[str] = Field("en", description="Language for generated explanation: en, hi, kn")


class KeypadSmsCheckResponse(BaseModel):
    risk_score: float
    risk_level: str  # SAFE, LOW, MEDIUM, HIGH, CRITICAL
    category: str
    matched_signatures: List[str]
    explanation: str
    recommended_action: str
    golden_rule: str
    helpline: str
    is_automatic_detection: bool = False
    disclaimer: str


# ── Call Check Schemas ───────────────────────────────────────────────────────

class KeypadCallCheckRequest(BaseModel):
    elderly_user_id: Optional[int] = Field(None, description="ID of protected elderly member if registered")
    phone_number: str = Field(..., min_length=7, max_length=50, description="Incoming phone number received on keypad phone")
    claimed_caller_identity: Optional[str] = Field(None, max_length=100, description="Who caller claimed to be (e.g., Police, Bank, Electricity Board)")
    preferred_language: Optional[str] = Field("en", description="Language for explanation: en, hi, kn")


class KeypadCallCheckResponse(BaseModel):
    phone_number: str
    normalized_number: str
    risk_level: str  # SAFE, LOW, MEDIUM, HIGH, CRITICAL, UNKNOWN
    risk_score: float
    fraud_category: Optional[str] = None
    report_count: int
    is_verified_authority: bool
    verification_status: str  # COMMUNITY_UNVERIFIED, CORROBORATED, OFFICIAL_AUTHORITY_VERIFIED, NO_REPORTS
    explanation: str
    recommended_action: str
    reporting_helpline: str
    is_automatic_blocking: bool = False
    disclaimer: str


# ── Scam Number Report Schemas ───────────────────────────────────────────────

class KeypadScamNumberReportRequest(BaseModel):
    elderly_user_id: Optional[int] = Field(None, description="Optional registered elderly user ID")
    phone_number: str = Field(..., min_length=7, max_length=50, description="Phone number to report")
    fraud_category: str = Field(default="SUSPICIOUS_CALL", description="DIGITAL_ARREST, BANK_KYC, ELECTRICITY_BILL, LOTTERY_PRIZE, PENSION_SCHEME, IMPERSONATION")
    claimed_caller_identity: Optional[str] = Field(None, max_length=100, description="Identity claimed by the scammer")
    evidence_notes: Optional[str] = Field(None, max_length=2000, description="Details of call/message received on elderly phone")


class KeypadScamNumberReportResponse(BaseModel):
    id: int
    normalized_number: str
    status: str
    message: str
    verification_status: str


# ── Guardian Alert & Incident Schemas ────────────────────────────────────────

class KeypadIncidentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    guardian_user_id: int
    elderly_user_id: Optional[int]
    elderly_user_name: Optional[str]
    incident_type: str
    indicator: str
    risk_score: float
    severity: str
    category: str
    explanation: str
    recommended_action: str
    is_acknowledged: bool
    created_at: datetime


class KeypadAlertSummaryResponse(BaseModel):
    total_dependents: int
    total_incidents: int
    unacknowledged_alerts: int
    critical_alerts: int
    high_alerts: int
    recent_incidents: List[KeypadIncidentResponse]


# ── Elderly Fraud Education Schemas ─────────────────────────────────────────

class KeypadEducationTopic(BaseModel):
    topic_id: str
    title: str
    summary: str
    danger_indicators: List[str]
    safe_behavior: str


class KeypadEducationResponse(BaseModel):
    language: str
    language_label: str
    golden_rule_title: str
    golden_rule_description: str
    do_not_share_items: List[str]
    common_scams: List[KeypadEducationTopic]
    helpline_guidance: str


# ── Official Reporting Guidance Schemas ──────────────────────────────────────

class HelpdeskEntry(BaseModel):
    name: str
    purpose: str
    access_channel: str
    contact_or_url: str
    how_it_helps: str


class KeypadOfficialHelpdeskResponse(BaseModel):
    disclaimer: str
    portals: List[Dict[str, Any]]
    helplines: List[HelpdeskEntry]
    legal_clarification: str
