"""
Cyber Raksha AI - Communication Pydantic Schemas
Defines request and response contracts for Stage 3 Communication Fraud Detection
and Digital Arrest Scam protection.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class CommunicationAnalyzeRequest(BaseModel):
    message: str = Field(
        ...,
        description="The content of the SMS, WhatsApp, Email, or suspicious chat message to evaluate.",
        examples=["Your bank account will be blocked immediately. Share your OTP."]
    )


class IndicatorsBreakdown(BaseModel):
    urgency_markers: int = Field(default=0)
    financial_markers: int = Field(default=0)
    impersonation_markers: int = Field(default=0)
    social_engineering_markers: int = Field(default=0)
    digital_arrest_markers: int = Field(default=0)


class CommunicationAnalysisDetail(BaseModel):
    latency_ms: Optional[float] = None
    model_algorithm: Optional[str] = None
    ml_fraud_probability: Optional[float] = None
    indicators_breakdown: Optional[IndicatorsBreakdown] = None
    is_digital_arrest_candidate: bool = Field(default=False)


class CommunicationAnalyzeResponse(BaseModel):
    success: bool = Field(..., description="Whether the analysis executed successfully.")
    classification: str = Field(..., description="Predicted category: DIGITAL_ARREST_SCAM, FINANCIAL_SCAM, IMPERSONATION, PHISHING, SUSPICIOUS, SAFE, or INCONCLUSIVE.")
    risk_level: str = Field(..., description="Qualitative risk tier: LOW, MEDIUM, HIGH, or CRITICAL.")
    risk_score: float = Field(..., description="Calculated multi-factor risk score (0.0 to 100.0 scale).")
    confidence: Optional[float] = Field(default=None, description="Statistical confidence score.")
    detected_indicators: List[str] = Field(default_factory=list, description="Specific identified fraud or social engineering markers.")
    explanation: str = Field(..., description="Evidence-backed explanation of the risk assessment.")
    recommendations: List[str] = Field(default_factory=list, description="Specific safety and mitigation actions for the user.")
    model_version: str = Field(..., description="Version of the active machine learning artifact.")
    analysis: Optional[CommunicationAnalysisDetail] = None


class CommunicationStatusResponse(BaseModel):
    model_available: bool
    model_loaded: bool
    model_version: str
    algorithm: str
    engine_stage: str
    training_status: str
    inference_status: str
    metrics_summary: Optional[Dict[str, Any]] = None

