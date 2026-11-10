"""
backend/app/api/routes/prevention.py
FastAPI routes for Stage 6: Proactive Threat Prevention & Incident Response.
"""
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.incident import SecurityIncident
from app.core.security import get_security_context, SecurityContext
from app.services.incident_service import IncidentService
from app.schemas.incident import (
    IncidentCreateRequest,
    IncidentUpdateRequest,
    IncidentDetailResponse,
    IncidentListResponse,
    IncidentActionSchema,
    IncidentAcknowledgeRequest,
    IncidentResolveRequest,
    IncidentFalsePositiveRequest,
    IncidentDisputeRequest,
    RecommendationRequest,
    AssistantGuidanceRequest,
    AssistantGuidanceResponse,
    ProtectionOverviewResponse
)
from ai_engine.prevention.prevention_engine import prevention_engine

router = APIRouter(tags=["Stage 6: Proactive Prevention & Incident Response"])


# 1. Incident Management Endpoints
@router.post(
    "/incidents",
    response_model=IncidentDetailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Security Incident",
    description="Registers a new security incident and automatically populates guided recovery actions."
)
def create_incident(
    request: IncidentCreateRequest,
    db: Session = Depends(get_db)
):
    return IncidentService.create_incident(request, db)


@router.get(
    "/incidents",
    response_model=IncidentListResponse,
    status_code=status.HTTP_200_OK,
    summary="List Security Incidents",
    description="Retrieve open and historical security incidents with optional status filter and multi-device scoping."
)
def get_incidents(
    limit: int = 50,
    status: Optional[str] = None,
    device_id: Optional[str] = None,
    sec_ctx: SecurityContext = Depends(get_security_context),
    db: Session = Depends(get_db)
):
    # Phase B3.1: Enforce device data isolation
    effective_device_id = device_id
    if sec_ctx.auth_type == "DEVICE":
        if device_id and device_id != sec_ctx.device_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Cannot query incidents for another device."
            )
        effective_device_id = sec_ctx.device_id

    return IncidentService.get_incidents(db, limit, status, device_id=effective_device_id)


@router.get(
    "/incidents/{incident_id}",
    response_model=IncidentDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Incident Details",
    description="Fetch full incident details and guided containment actions with authorization check."
)
def get_incident_by_id(
    incident_id: int,
    sec_ctx: SecurityContext = Depends(get_security_context),
    db: Session = Depends(get_db)
):
    raw_inc = db.query(SecurityIncident).filter(SecurityIncident.id == incident_id).first()
    if not raw_inc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident with ID {incident_id} not found."
        )
    if not sec_ctx.can_access_incident(raw_inc):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Incident belongs to another registered device."
        )
    return IncidentService._format_incident(raw_inc)


@router.patch(
    "/incidents/{incident_id}",
    response_model=IncidentDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Update Incident Status",
    description="Update incident lifecycle status (e.g. RESOLVED, CLOSED) and add resolution notes."
)
def update_incident(
    incident_id: int,
    request: IncidentUpdateRequest,
    sec_ctx: SecurityContext = Depends(get_security_context),
    db: Session = Depends(get_db)
):
    raw_inc = db.query(SecurityIncident).filter(SecurityIncident.id == incident_id).first()
    if not raw_inc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident with ID {incident_id} not found."
        )
    if not sec_ctx.can_access_incident(raw_inc):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Cannot update incident belonging to another device."
        )

    updated = IncidentService.update_incident(incident_id, request, db)
    return updated


@router.post(
    "/incidents/{incident_id}/acknowledge",
    response_model=IncidentDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Acknowledge Incident",
    description="User confirms viewing the security incident; transitions status to INVESTIGATING."
)
def acknowledge_incident(
    incident_id: int,
    request: IncidentAcknowledgeRequest = None,
    sec_ctx: SecurityContext = Depends(get_security_context),
    db: Session = Depends(get_db)
):
    raw_inc = db.query(SecurityIncident).filter(SecurityIncident.id == incident_id).first()
    if not raw_inc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident with ID {incident_id} not found."
        )
    if not sec_ctx.can_access_incident(raw_inc):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Cannot acknowledge incident belonging to another device."
        )

    user_or_dev = sec_ctx.device_id or (request.user_or_device if request else None)
    notes = request.notes if request else None
    acked = IncidentService.acknowledge_incident(incident_id, db, user_or_device=user_or_dev, notes=notes)
    return acked


@router.post(
    "/incidents/{incident_id}/resolve",
    response_model=IncidentDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Resolve Incident",
    description="Marks a security incident as resolved with resolution notes."
)
def resolve_incident(
    incident_id: int,
    request: IncidentResolveRequest,
    sec_ctx: SecurityContext = Depends(get_security_context),
    db: Session = Depends(get_db)
):
    raw_inc = db.query(SecurityIncident).filter(SecurityIncident.id == incident_id).first()
    if not raw_inc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident with ID {incident_id} not found."
        )
    if not sec_ctx.can_access_incident(raw_inc):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Cannot resolve incident belonging to another device."
        )

    user_or_dev = sec_ctx.device_id or request.user_or_device
    resolved = IncidentService.resolve_incident(
        incident_id=incident_id,
        resolution_notes=request.resolution_notes,
        db=db,
        user_or_device=user_or_dev
    )
    return resolved


@router.post(
    "/incidents/{incident_id}/dispute",
    response_model=IncidentDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Dispute Incident",
    description="User records a dispute against an incident. Preserves evidence without erasing global authoritative threat intelligence."
)
def dispute_incident(
    incident_id: int,
    request: IncidentDisputeRequest,
    sec_ctx: SecurityContext = Depends(get_security_context),
    db: Session = Depends(get_db)
):
    raw_inc = db.query(SecurityIncident).filter(SecurityIncident.id == incident_id).first()
    if not raw_inc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident with ID {incident_id} not found."
        )
    if not sec_ctx.can_access_incident(raw_inc):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Cannot dispute incident belonging to another device."
        )

    user_or_dev = sec_ctx.device_id or request.user_or_device
    disputed = IncidentService.dispute_incident(
        incident_id=incident_id,
        reason=request.reason,
        db=db,
        user_or_device=user_or_dev
    )
    return disputed


@router.post(
    "/incidents/{incident_id}/false-positive",
    response_model=IncidentDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Mark Incident False Positive",
    description="Flags an incident as a false positive. Only administrators can de-list global authoritative indicators."
)
def mark_incident_false_positive(
    incident_id: int,
    request: IncidentFalsePositiveRequest,
    sec_ctx: SecurityContext = Depends(get_security_context),
    db: Session = Depends(get_db)
):
    raw_inc = db.query(SecurityIncident).filter(SecurityIncident.id == incident_id).first()
    if not raw_inc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident with ID {incident_id} not found."
        )
    if not sec_ctx.can_access_incident(raw_inc):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Cannot mark false positive on incident belonging to another device."
        )

    user_or_dev = sec_ctx.device_id or request.user_or_device
    fp = IncidentService.mark_false_positive(
        incident_id=incident_id,
        reason=request.reason,
        db=db,
        user_or_device=user_or_dev,
        is_admin=sec_ctx.is_admin
    )
    return fp


# 2. Prevention & Recommendations Endpoints
@router.post(
    "/prevention/recommendations",
    status_code=status.HTTP_200_OK,
    summary="Generate Dynamic Prevention Recommendations",
    description="Generates immediate, short-term, and long-term actions tailored to detected threat evidence."
)
def generate_threat_recommendations(request: RecommendationRequest):
    return prevention_engine.create_recommendations(
        classification=request.classification,
        risk_level=request.risk_level,
        risk_score=request.risk_score,
        threat_category=request.threat_category,
        detected_indicators=request.detected_indicators,
        threat_intel_matches=request.threat_intel_matches
    )


@router.get(
    "/prevention/playbooks",
    status_code=status.HTTP_200_OK,
    summary="List Incident Response Playbooks",
    description="Retrieve all guided response playbooks for phishing, financial fraud, and digital arrest."
)
def get_playbooks():
    return prevention_engine.get_playbooks()


@router.post(
    "/prevention/actions/{action_id}/complete",
    response_model=IncidentActionSchema,
    status_code=status.HTTP_200_OK,
    summary="Complete Guided Incident Action",
    description="Marks a specific user-confirmed mitigation action as completed and updates incident containment status."
)
def complete_incident_action(
    action_id: int,
    db: Session = Depends(get_db)
):
    action = IncidentService.complete_action(action_id, db)
    if not action:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident action with ID {action_id} not found."
        )
    return action


# 3. Personal Security Center & Security Guidance Assistant
@router.get(
    "/protection/overview",
    response_model=ProtectionOverviewResponse,
    status_code=status.HTTP_200_OK,
    summary="Personal Protection Center Overview",
    description="Returns aggregate posture score, open incidents, and pending actions."
)
def get_protection_overview(db: Session = Depends(get_db)):
    return IncidentService.get_protection_overview(db)


@router.post(
    "/assistant/security-guidance",
    response_model=AssistantGuidanceResponse,
    status_code=status.HTTP_200_OK,
    summary="Security Guidance Assistant",
    description="Answers security questions regarding clicked links, shared OTPs, and fake police calls using verified security doctrine."
)
def get_security_guidance(request: AssistantGuidanceRequest):
    return prevention_engine.ask_assistant(request.query, request.context)

