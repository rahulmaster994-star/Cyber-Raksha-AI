"""
Cyber Raksha AI - Unified Security Event & Risk API Routes
Phase B3: Unified Protection Integration
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.database.session import get_db
from app.core.security import get_security_context, SecurityContext
from app.models.security_event import SecurityEvent
from app.schemas.security_event import (
    SecurityEventCreate,
    SecurityEventResponse,
    SecurityEventListResponse,
    UnifiedRiskEvaluationRequest,
    UnifiedRiskEvaluationResponse
)
from app.services.central_risk_engine import central_risk_engine
from app.services.notification_service import notification_service

router = APIRouter(prefix="/security", tags=["Unified Protection & Security Engine (Phase B3)"])


@router.post(
    "/events",
    response_model=SecurityEventResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Ingest Unified Security Event",
    description="Receives security events from Browser Extension, Android App, or internal components. Correlates with threat intelligence and manages incidents."
)
def ingest_security_event(
    payload: SecurityEventCreate,
    request: Request,
    db: Session = Depends(get_db)
):
    if not payload.source_ip and request.client:
        payload.source_ip = request.client.host

    event = central_risk_engine.process_security_event(db, payload)
    return event


@router.get(
    "/events",
    response_model=SecurityEventListResponse,
    status_code=status.HTTP_200_OK,
    summary="List Security Events",
    description="Retrieves persistent audit log of security events across all components with strict multi-device isolation."
)
def list_security_events(
    source_component: Optional[str] = Query(None, description="Filter by BROWSER_EXTENSION | ANDROID_APP | THREAT_INTEL_FEED | CENTRAL_RISK_ENGINE"),
    severity: Optional[str] = Query(None, description="Filter by severity level"),
    device_id: Optional[str] = Query(None, description="Filter by registered device identifier"),
    limit: int = Query(50, ge=1, le=200),
    sec_ctx: SecurityContext = Depends(get_security_context),
    db: Session = Depends(get_db)
):
    query = db.query(SecurityEvent)

    # Phase B3.1: Enforce device data isolation
    if sec_ctx.auth_type == "DEVICE":
        if device_id and device_id != sec_ctx.device_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: Cannot query security events for device '{device_id}'."
            )
        # Device callers can only see their own device events or global system events
        query = query.filter((SecurityEvent.device_id == sec_ctx.device_id) | (SecurityEvent.device_id.is_(None)))
    elif device_id:
        query = query.filter(SecurityEvent.device_id == device_id)

    if source_component:
        query = query.filter(SecurityEvent.source_component == source_component.upper())
    if severity:
        query = query.filter(SecurityEvent.severity == severity.upper())

    total = query.count()
    events = query.order_by(desc(SecurityEvent.created_at)).limit(limit).all()

    return SecurityEventListResponse(
        total=total,
        events=events
    )


@router.post(
    "/risk/evaluate",
    response_model=UnifiedRiskEvaluationResponse,
    status_code=status.HTTP_200_OK,
    summary="Evaluate Unified Threat Risk",
    description="Synthesizes cross-vector evidence (threat intelligence, caller reputation, heuristics) without double-counting."
)
def evaluate_unified_risk(
    payload: UnifiedRiskEvaluationRequest,
    db: Session = Depends(get_db)
):
    result = central_risk_engine.evaluate_risk(db, payload)
    return result


@router.post(
    "/stream-ticket",
    status_code=status.HTTP_201_CREATED,
    summary="Issue Single-Use SSE Connection Ticket",
    description="Generates a cryptographically random, short-lived (60s), single-use connection ticket for secure browser EventSource connections without exposing persistent tokens in URLs."
)
def create_stream_ticket(
    sec_ctx: SecurityContext = Depends(get_security_context)
):
    if not sec_ctx.is_authenticated:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to request an SSE stream ticket. Provide X-Device-Token or X-Admin-Key."
        )

    from app.services.ticket_service import ticket_service
    ticket = ticket_service.create_ticket(
        device_id=sec_ctx.device_id,
        is_admin=sec_ctx.is_admin,
        auth_type=sec_ctx.auth_type
    )

    return {
        "ticket": ticket,
        "expires_in_seconds": 60,
        "scope": "ADMIN" if sec_ctx.is_admin else "DEVICE",
        "device_id": sec_ctx.device_id
    }


@router.get(
    "/stream",
    summary="Real-Time Security Event Stream (SSE)",
    description="Streams real-time threat notifications, security events, and incident updates with strict multi-device authorization scoping. Requires either standard auth headers or a single-use ticket in ?ticket=."
)
async def security_event_stream(
    target_device: Optional[str] = Query(None, description="Target device ID to scope private stream"),
    ticket: Optional[str] = Query(None, description="Single-use short-lived connection ticket obtained via POST /security/stream-ticket"),
    sec_ctx: SecurityContext = Depends(get_security_context)
):
    # Phase B3.1: Enforce device authorization on private SSE streams
    if target_device and sec_ctx.is_authenticated and not sec_ctx.can_access_device(target_device):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied: Cannot subscribe to private SSE stream for device '{target_device}'."
        )

    effective_device_id = sec_ctx.device_id or target_device

    return StreamingResponse(
        notification_service.stream_notifications(
            client_device_id=effective_device_id,
            is_admin=sec_ctx.is_admin
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

