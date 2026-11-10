"""
Cyber Raksha AI - Detection Pydantic Schemas
Defines request and response contracts for Stage 2 Phishing & URL Detection.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class URLDetectionRequest(BaseModel):
    """
    Input schema for URL threat analysis.
    """
    url: str = Field(
        ...,
        description="The target web address to evaluate for phishing and malicious indicators.",
        examples=["https://example.com"]
    )


class URLAnalysisDetail(BaseModel):
    features: Dict[str, Any] = Field(default_factory=dict, description="Lexical and structural characteristics extracted from the URL.")
    risk_indicators: List[str] = Field(default_factory=list, description="Specific heuristic flags and behavioral risk markers.")
    latency_ms: Optional[float] = Field(default=None, description="Inference and processing latency in milliseconds.")
    ml_probabilities: Optional[Dict[str, float]] = Field(default=None, description="Raw model probability outputs.")
    model_algorithm: Optional[str] = Field(default=None, description="Algorithm powering the active classification.")
    feature_count: Optional[int] = Field(default=None, description="Number of evaluated feature dimensions.")
    brand_impersonation: Optional[Dict[str, Any]] = Field(default=None, description="Brand impersonation diagnostic if detected.")


class URLDetectionResponse(BaseModel):
    """
    Standardized response format as required by the Stage 2 specification.
    """
    success: bool = Field(..., description="Whether the detection completed successfully.")
    classification: str = Field(..., description="Predicted class: LEGITIMATE, PHISHING, SUSPICIOUS, or INCONCLUSIVE.")
    risk_level: str = Field(..., description="Qualitative risk tier: LOW, SUSPICIOUS, HIGH, or UNKNOWN.")
    risk_score: float = Field(..., description="Calculated composite risk score on a 0.0 to 100.0 scale.")
    model_version: str = Field(..., description="Active machine learning model artifact identifier.")
    confidence: Optional[float] = Field(default=None, description="Statistical confidence score of the prediction.")
    analysis: URLAnalysisDetail = Field(..., description="Detailed diagnostic breakdown.")
    recommendation: str = Field(..., description="Actionable security guidance for end users and analysts.")


class DetectionStatusResponse(BaseModel):
    """
    Operational health and availability contract for the AI detector.
    """
    model_available: bool = Field(..., description="Whether model weights exist on disk.")
    model_loaded: bool = Field(..., description="Whether the model is instantiated in memory.")
    model_version: str = Field(..., description="Currently deployed model version.")
    algorithm: str = Field(..., description="Winning model algorithm architecture.")
    training_status: str = Field(..., description="Training status of the local engine.")
    engine_stage: str = Field(..., description="Development stage of the AI subsystem.")
    dataset_status: str = Field(..., description="Status of benchmark and raw feeds.")
    inference_status: str = Field(..., description="Live inference readiness.")
    metrics_summary: Optional[Dict[str, Any]] = Field(default=None, description="Independent test set evaluation metrics.")


class AnalysisHistoryItem(BaseModel):
    """
    Schema representing a recorded analysis event in the database.
    """
    model_config = ConfigDict(from_attributes=True)

    id: int
    module_code: str
    target_identifier: str
    status: str
    risk_score: Optional[float] = None
    threat_category: Optional[str] = None
    summary: Optional[str] = None
    explanation: Optional[str] = None
    created_at: datetime


class AnalysisHistoryResponse(BaseModel):
    total_records: int
    records: List[AnalysisHistoryItem]
