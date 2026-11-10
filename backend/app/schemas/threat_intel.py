"""
backend/app/schemas/threat_intel.py
Pydantic schemas for Stage 5: Threat Intelligence & Unified Risk Assessment.
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class ThreatIndicatorSchema(BaseModel):
    indicator_type: str
    indicator_value: str
    threat_type: str
    severity: str
    confidence_score: float
    source_name: str
    source_reference: Optional[str] = None
    description: Optional[str] = None
    is_active: bool = True
    first_seen: Optional[str] = None
    last_seen: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ThreatSearchRequest(BaseModel):
    query: str = Field(..., min_length=2, max_length=512)
    indicator_type: Optional[str] = None  # URL, DOMAIN, IP, or None for auto-detect


class ThreatSearchResponse(BaseModel):
    query: str
    indicator_type: str
    is_threat_found: bool
    matched_indicator: Optional[ThreatIndicatorSchema] = None
    source: Optional[str] = None
    severity: Optional[str] = None
    search_timestamp: str


class ThreatIntelStatusResponse(BaseModel):
    module: str = "THREAT_INTEL"
    engine_stage: str = "STAGE_5"
    service_status: str = "OPERATIONAL"
    total_active_indicators: int
    by_type: Dict[str, int]
    sources: List[str]
    last_feed_update: Optional[str] = None
    feed_updater_status: str = "IDLE"
    auto_sync_enabled: bool = True
    sync_interval_minutes: int = 60
    next_scheduled_sync: Optional[str] = None
    scheduler_status: str = "IDLE"


class UnifiedAnalyzeRequest(BaseModel):
    url: Optional[str] = None
    message: Optional[str] = None
    is_digital_arrest: bool = False


class UnifiedAnalyzeResponse(BaseModel):
    overall_risk_level: str
    overall_risk_score: float
    threat_category: str
    is_corroborated: bool
    corroboration_notes: List[str]
    intel_matches_count: int
    intel_matches: List[Dict[str, Any]]
    evidence_chain: List[Dict[str, Any]]
    factual_evidence: Optional[List[str]] = Field(default_factory=list)
    model_predictions: Optional[List[str]] = Field(default_factory=list)
    negative_findings: Optional[List[str]] = Field(default_factory=list)
    unavailable_information: Optional[List[str]] = Field(default_factory=list)
    uncertainty_factors: Optional[List[str]] = Field(default_factory=list)
    limitations: Optional[List[str]] = Field(default_factory=list)
    conflict_notes: Optional[List[str]] = Field(default_factory=list)
    extracted_indicators: Dict[str, List[str]]
    modules: Dict[str, Any]
    explanation: str
    recommended_actions: List[str]
    analysis_timestamp: str


class LiveThreatEvent(BaseModel):
    id: int
    event_type: str
    severity: str
    source_component: str
    description: str
    created_at: str

    model_config = ConfigDict(from_attributes=True)

