"""
Cyber Raksha AI - Unified Security Event Schemas
Phase B3: Unified Protection Integration
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class SecurityEventCreate(BaseModel):
    event_type: str = Field(..., description="BROWSER_BLOCKED_URL | SMS_FRAUD_DETECTED | CALL_FRAUD_DETECTED | THREAT_INTEL_MATCH | DEVICE_REVOKED")
    severity: str = Field(default="MEDIUM", description="LOW | MEDIUM | HIGH | CRITICAL | SAFE")
    source_component: str = Field(..., description="BROWSER_EXTENSION | ANDROID_APP | THREAT_INTEL_FEED | CENTRAL_RISK_ENGINE")
    device_id: Optional[str] = Field(None, description="Registered device identifier where applicable")
    threat_indicator: Optional[str] = Field(None, description="Target URL, domain, phone number, or hash")
    risk_score: float = Field(default=0.0, ge=0.0, le=100.0)
    detection_reason: Optional[str] = Field(None, description="Primary explanation for threat classification")
    source_ip: Optional[str] = Field(None)
    description: str = Field(..., min_length=1)
    raw_payload: Optional[str] = Field(None)


class SecurityEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    event_id: str
    event_type: str
    severity: str
    source_component: str
    device_id: Optional[str]
    threat_indicator: Optional[str]
    risk_score: float
    detection_reason: Optional[str]
    source_ip: Optional[str]
    description: str
    is_resolved: bool
    verification_status: str
    incident_id: Optional[int]
    processing_status: str
    created_at: datetime


class SecurityEventListResponse(BaseModel):
    total: int
    events: List[SecurityEventResponse]


class UnifiedRiskEvaluationRequest(BaseModel):
    indicator: str = Field(..., description="URL, domain, or phone number to evaluate")
    indicator_type: str = Field(..., description="URL | DOMAIN | PHONE_NUMBER | SMS_CONTENT")
    source_component: str = Field(..., description="Component requesting evaluation")
    device_id: Optional[str] = None
    context_data: Optional[Dict[str, Any]] = None


class UnifiedRiskEvaluationResponse(BaseModel):
    indicator: str
    indicator_type: str
    risk_level: str
    risk_score: float
    confidence_score: float
    fraud_category: Optional[str]
    detection_reasons: List[str]
    corroborating_sources: List[str]
    is_verified_threat: bool
    recommended_action: str
    incident_id: Optional[int]
    evaluated_at: datetime
    # Phase B4: Intelligent Threat Detection Explainability
    classification: Optional[str] = "UNKNOWN"
    intelligence_status: Optional[str] = "NOT_CONFIRMED"
    evidence_items: Optional[List[Dict[str, Any]]] = Field(default_factory=list)

