"""
backend/app/schemas/audio.py
Pydantic schemas for Stage 4 Audio Detection endpoints.
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class AudioMetadataSchema(BaseModel):
    filename: Optional[str] = None
    file_size_bytes: Optional[int] = None
    duration_seconds: Optional[float] = None
    sample_rate: Optional[int] = None
    channels: Optional[int] = None
    bit_depth: Optional[int] = None
    format: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class AudioIndicatorSchema(BaseModel):
    code: str
    name: str
    severity: str
    description: str
    score_weight: int


class AudioAnalysisResponse(BaseModel):
    status: str = "SUCCESS"
    classification: str
    risk_level: str
    risk_score: float
    confidence: float
    ml_probability: float
    indicator_score: float
    indicators_count: int
    detected_indicators: List[AudioIndicatorSchema]
    spectral_metrics: Dict[str, Any]
    audio_metadata: AudioMetadataSchema
    explanation: str
    recommendations: List[str]
    is_inconclusive: bool = False
    inconclusive_reason: Optional[str] = None
    engine_version: str
    model_version: Optional[str] = None
    forensic_capability_scope: str = Field(
        default="ACOUSTIC_VOCODER_ARTIFACT_ANALYSIS_ONLY",
        description="Explicit scope: evaluates synthetic vocoder and acoustic anomalies only; does NOT verify biometric speaker identity."
    )
    biometric_identity_supported: bool = Field(
        default=False,
        description="Whether biometric voiceprint identity verification is performed (strictly False)."
    )

    model_config = ConfigDict(from_attributes=True)


class AudioStatusResponse(BaseModel):
    module: str
    model_available: bool
    model_loaded: bool
    model_name: str
    model_type: str
    stage: str
    accuracy: Optional[float] = None
    features_count: int
    supported_formats: List[str]
    disclaimer: str
    forensic_capability_scope: str = Field(
        default="ACOUSTIC_VOCODER_ARTIFACT_ANALYSIS_ONLY",
        description="Explicit scope: evaluates synthetic vocoder and acoustic anomalies only; does NOT verify biometric speaker identity."
    )
    biometric_identity_supported: bool = Field(
        default=False,
        description="Whether biometric voiceprint identity verification is performed (strictly False)."
    )

    model_config = ConfigDict(from_attributes=True)

