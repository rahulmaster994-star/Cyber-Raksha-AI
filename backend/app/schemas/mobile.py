"""
Cyber Raksha AI - Mobile Fraud Protection Schemas
Phase B2: Intelligent SMS & Call Fraud Protection
"""
import re
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class ExtractedUrlThreat(BaseModel):
    url: str
    is_malicious: bool
    threat_type: Optional[str] = None
    source: Optional[str] = None


class MessageAnalysisRequest(BaseModel):
    device_id: str = Field(..., min_length=16, max_length=64, description="Registered device identifier.")
    message_text: str = Field(..., min_length=1, max_length=4000, description="SMS content for heuristic and threat intel analysis.")
    sender: Optional[str] = Field(None, max_length=50, description="SMS sender header or originating number.")

    @field_validator("message_text")
    @classmethod
    def sanitize_message_text(cls, v: str) -> str:
        clean = v.strip()
        if not clean:
            raise ValueError("message_text cannot be empty.")
        return clean


class MessageAnalysisResponse(BaseModel):
    message_hash: str
    risk_score: float = Field(..., ge=0.0, le=100.0)
    risk_level: str = Field(..., description="CRITICAL, HIGH, MEDIUM, LOW, SAFE")
    fraud_category: str = Field(..., description="BANKING_FRAUD, UPI_FRAUD, OTP_FRAUD, DELIVERY_SCAM, LOTTERY_SCAM, GOV_IMPERSONATION, BENIGN")
    detection_reasons: List[str]
    extracted_urls: List[str]
    url_threats: List[ExtractedUrlThreat]
    recommended_action: str
    analyzed_at: datetime


class NumberCheckRequest(BaseModel):
    device_id: str = Field(..., min_length=16, max_length=64, description="Registered device identifier.")
    phone_number: str = Field(..., min_length=3, max_length=30, description="Incoming phone number to verify.")

    @field_validator("phone_number")
    @classmethod
    def sanitize_phone_number(cls, v: str) -> str:
        clean = v.strip()
        if not clean:
            raise ValueError("phone_number cannot be empty.")
        return clean


class NumberCheckResponse(BaseModel):
    phone_number: str
    normalized_number: str
    risk_level: str = Field(..., description="CRITICAL, HIGH, MEDIUM, LOW, SAFE, UNKNOWN")
    fraud_category: Optional[str] = None
    report_count: int = 0
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    source: str
    is_verified_authority: bool = False
    classification_reason: Optional[str] = None
    dispute_count: int = 0
    notes: Optional[str] = None
    recommended_action: str
    checked_at: datetime


class DisputeNumberRequest(BaseModel):
    device_id: str = Field(..., min_length=16, max_length=64)
    phone_number: str = Field(..., min_length=3, max_length=30)
    reason: Optional[str] = Field(None, max_length=500, description="Explanation of why this is a legitimate contact")


class DisputeNumberResponse(BaseModel):
    success: bool
    message: str
    phone_number: str
    current_risk_level: str
    dispute_count: int


class ReportThreatRequest(BaseModel):
    device_id: str = Field(..., min_length=16, max_length=64)
    threat_type: str = Field(..., description="PHONE_NUMBER, SMS_SENDER, MALICIOUS_URL")
    indicator_value: str = Field(..., min_length=3, max_length=512)
    fraud_category: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = Field(None, max_length=1000)

    @field_validator("threat_type")
    @classmethod
    def validate_threat_type(cls, v: str) -> str:
        v_upper = v.upper()
        if v_upper not in {"PHONE_NUMBER", "SMS_SENDER", "MALICIOUS_URL"}:
            raise ValueError("threat_type must be PHONE_NUMBER, SMS_SENDER, or MALICIOUS_URL")
        return v_upper


class ReportThreatResponse(BaseModel):
    success: bool
    message: str
    indicator_value: str
    report_id: Optional[int] = None


class ThreatHistoryItem(BaseModel):
    id: int
    threat_type: str  # SMS or CALL
    target_or_hash: str
    risk_level: str
    risk_score: float
    fraud_category: str
    detection_reasons: List[str]
    timestamp: datetime


class ThreatHistoryResponse(BaseModel):
    device_id: str
    total: int
    items: List[ThreatHistoryItem]


class ProtectionStatusResponse(BaseModel):
    device_id: str
    sms_protection: str = Field(default="ACTIVE", description="ACTIVE, PERMISSION_REQUIRED, MANUAL_ONLY, NOT_SUPPORTED")
    call_protection: str = Field(default="ACTIVE", description="ACTIVE, PERMISSION_REQUIRED, NOT_SUPPORTED")
    database_signatures_count: int = 0
    phone_reputation_entries: int = 0
    last_sync: Optional[datetime] = None

