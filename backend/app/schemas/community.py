"""
Cyber Raksha AI - Community Intelligence Schemas
"""
from typing import Optional
from pydantic import BaseModel, Field


class CommunityReportRequest(BaseModel):
    indicator: str = Field(..., min_length=2, max_length=255, description="Phone number, domain, UPI ID, or sender ID")
    indicator_type: str = Field(..., description="PHONE, URL, UPI, SMS_SENDER, TELEGRAM")
    category: str = Field(..., description="e.g. BANKING_FRAUD, DIGITAL_ARREST, LOTTERY, EXTORTION")
    description: Optional[str] = None
    severity: str = Field("HIGH", description="LOW, MEDIUM, HIGH, CRITICAL")
    device_id: Optional[str] = None


class CommunityReportResponse(BaseModel):
    indicator: str
    indicator_type: str
    category: str
    total_reports: int
    severity: str
    verified_status: str
    status: str = "RECORDED"
    message: str


class IndicatorReputationResponse(BaseModel):
    indicator: str
    indicator_type: str
    is_malicious: bool
    risk_score: float
    total_reports: int
    top_categories: list[str]
    reputation_status: str

