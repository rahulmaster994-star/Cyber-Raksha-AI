"""
backend/app/schemas/incident.py
Pydantic V2 schemas for Stage 6 Security Incidents, Guided Playbooks,
and Personal Protection Center.
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class IncidentActionSchema(BaseModel):
    id: int
    action_key: str
    title: str
    description: str
    priority: str
    is_completed: bool
    completed_at: Optional[str] = None
    created_at: str

    model_config = ConfigDict(from_attributes=True)


class IncidentCreateRequest(BaseModel):
    category: str = Field(..., min_length=2, max_length=100)
    title: str = Field(..., min_length=5, max_length=255)
    severity: str = Field(default="HIGH")  # LOW, MEDIUM, HIGH, CRITICAL
    summary: str = Field(..., min_length=10)
    related_analysis_id: Optional[int] = None
    evidence_references: Optional[str] = None
    playbook_id: Optional[str] = None  # Optional playbook to auto-populate actions


class IncidentUpdateRequest(BaseModel):
    status: Optional[str] = None  # NEW, UNDER_INVESTIGATION, ACTION_REQUIRED, CONTAINMENT_IN_PROGRESS, RECOVERY_IN_PROGRESS, RESOLVED, CLOSED
    resolution_notes: Optional[str] = None


class IncidentDetailResponse(BaseModel):
    id: int
    incident_number: str
    category: str
    title: str
    severity: str
    status: str
    summary: str
    target_or_indicator: Optional[str] = None
    source_components: Optional[List[str]] = []
    device_id: Optional[str] = None
    user_acknowledged: bool = False
    acknowledged_at: Optional[str] = None
    is_false_positive: bool = False
    related_analysis_id: Optional[int] = None
    evidence_references: Optional[str] = None
    resolution_notes: Optional[str] = None
    resolved_at: Optional[str] = None
    created_at: str
    updated_at: str
    actions: List[IncidentActionSchema] = []

    model_config = ConfigDict(from_attributes=True)


class IncidentAcknowledgeRequest(BaseModel):
    user_or_device: Optional[str] = None
    notes: Optional[str] = None


class IncidentResolveRequest(BaseModel):
    resolution_notes: str = Field(..., min_length=3)
    user_or_device: Optional[str] = None


class IncidentFalsePositiveRequest(BaseModel):
    reason: str = Field(..., min_length=3)
    user_or_device: Optional[str] = None


class IncidentDisputeRequest(BaseModel):
    reason: str = Field(..., min_length=3)
    user_or_device: Optional[str] = None


class IncidentListResponse(BaseModel):
    total_count: int
    incidents: List[IncidentDetailResponse]


class RecommendationRequest(BaseModel):
    classification: str
    risk_level: str
    risk_score: float
    threat_category: Optional[str] = None
    detected_indicators: Optional[List[str]] = []
    threat_intel_matches: Optional[List[Dict[str, Any]]] = []


class AssistantGuidanceRequest(BaseModel):
    query: str = Field(..., min_length=3, max_length=1000)
    context: Optional[Dict[str, Any]] = None


class AssistantGuidanceResponse(BaseModel):
    query: str
    category: str
    guidance_summary: str
    action_steps: List[str]
    official_resources: List[Dict[str, str]]
    disclaimer: str


class ProtectionOverviewResponse(BaseModel):
    active_incidents_count: int
    resolved_incidents_count: int
    pending_actions_count: int
    completed_actions_count: int
    security_posture_score: float  # 0 to 100
    recent_incidents: List[IncidentDetailResponse]
    available_playbooks_count: int
    privacy_mode: str

