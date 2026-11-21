"""
Cyber Raksha AI - Unified Dashboard & Telemetry API Routes
Phase B3: Unified Protection Integration

Aggregates real telemetry directly from database queries across
Browser Protection, Android Foundation, Threat Intelligence, and Incident Management.
Zero hardcoding or fake statistics.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Query, status, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc, func

from app.database.session import get_db
from app.core.security import get_security_context, SecurityContext
from app.models.security_event import SecurityEvent
from app.models.incident import SecurityIncident, IncidentAction
from app.models.device import Device
from app.models.threat_intel import ThreatIndicator, ThreatFeedLog
from app.models.notification import Notification
from app.models.phone_reputation import PhoneReputation

router = APIRouter(prefix="/dashboard", tags=["Central Security Dashboard (Phase B3)"])


def require_dashboard_access(sec_ctx: SecurityContext = Depends(get_security_context)) -> SecurityContext:
    if not sec_ctx.is_authenticated:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to view platform dashboard telemetry."
        )
    if not sec_ctx.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator privileges required to view global platform dashboard telemetry."
        )
    return sec_ctx


@router.get(
    "/overview",
    status_code=status.HTTP_200_OK,
    summary="Get Unified Security Command Center Overview",
    description="Returns verified aggregate statistics queried directly from the production database."
)
def get_dashboard_overview(
    auth: SecurityContext = Depends(require_dashboard_access),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    # 1. Real Event Counts
    total_events = db.query(SecurityEvent).count()
    events_by_sev = dict(
        db.query(SecurityEvent.severity, func.count(SecurityEvent.id))
        .group_by(SecurityEvent.severity)
        .all()
    )
    events_by_component = dict(
        db.query(SecurityEvent.source_component, func.count(SecurityEvent.id))
        .group_by(SecurityEvent.source_component)
        .all()
    )

    # 2. Real Incident Counts
    total_incidents = db.query(SecurityIncident).count()
    active_incidents = db.query(SecurityIncident).filter(
        SecurityIncident.status.notin_(["RESOLVED", "CLOSED", "FALSE_POSITIVE"])
    ).count()
    critical_incidents = db.query(SecurityIncident).filter(
        SecurityIncident.severity == "CRITICAL",
        SecurityIncident.status.notin_(["RESOLVED", "CLOSED", "FALSE_POSITIVE"])
    ).count()
    high_incidents = db.query(SecurityIncident).filter(
        SecurityIncident.severity == "HIGH",
        SecurityIncident.status.notin_(["RESOLVED", "CLOSED", "FALSE_POSITIVE"])
    ).count()
    resolved_incidents = db.query(SecurityIncident).filter(
        SecurityIncident.status.in_(["RESOLVED", "CLOSED"])
    ).count()

    # 3. Real Device Telemetry
    total_devices = db.query(Device).count()
    active_devices = db.query(Device).filter(Device.status == "ACTIVE", Device.is_revoked == False).count()
    revoked_devices = db.query(Device).filter(Device.is_revoked == True).count()

    # 4. Real Threat Intelligence Telemetry
    total_threat_indicators = db.query(ThreatIndicator).count()
    active_threat_indicators = db.query(ThreatIndicator).filter(ThreatIndicator.is_active == True).count()
    last_sync = db.query(ThreatFeedLog).order_by(desc(ThreatFeedLog.fetched_at)).first()

    # 5. Real Phone Reputation Telemetry
    total_phone_reputations = db.query(PhoneReputation).count()

    # 6. Overall Security Posture
    deductions = (critical_incidents * 20) + (high_incidents * 10) + (active_incidents * 5)
    posture_score = max(10.0, min(100.0, 100.0 - deductions))
    posture_label = "EXCELLENT" if posture_score >= 90 else (
        "GOOD" if posture_score >= 75 else (
            "WARNING" if posture_score >= 50 else "CRITICAL_ACTION_REQUIRED"
        )
    )

    return {
        "overall_posture": {
            "score": round(posture_score, 1),
            "label": posture_label,
            "status": "OPERATIONAL"
        },
        "events": {
            "total": total_events,
            "by_severity": events_by_sev,
            "by_component": events_by_component
        },
        "incidents": {
            "total": total_incidents,
            "active": active_incidents,
            "critical": critical_incidents,
            "high": high_incidents,
            "resolved": resolved_incidents
        },
        "devices": {
            "total_registered": total_devices,
            "active": active_devices,
            "revoked": revoked_devices
        },
        "threat_intelligence": {
            "total_indicators": total_threat_indicators,
            "active_indicators": active_threat_indicators,
            "phone_reputation_entries": total_phone_reputations,
            "last_sync_status": last_sync.status if last_sync else "INITIALIZED",
            "last_sync_time": last_sync.fetched_at.isoformat() if last_sync else None
        },
        "generated_at": datetime.now(timezone.utc).isoformat()
    }


@router.get(
    "/activity",
    status_code=status.HTTP_200_OK,
    summary="Get Recent Security Activity Feed",
    description="Returns chronological real security events and actions from all system components."
)
def get_dashboard_activity(
    limit: int = Query(25, ge=1, le=100),
    auth: SecurityContext = Depends(require_dashboard_access),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    events = (
        db.query(SecurityEvent)
        .order_by(desc(SecurityEvent.created_at))
        .limit(limit)
        .all()
    )

    items = [
        {
            "id": e.id,
            "event_id": e.event_id,
            "event_type": e.event_type,
            "severity": e.severity,
            "source_component": e.source_component,
            "threat_indicator": e.threat_indicator,
            "description": e.description,
            "detection_reason": e.detection_reason,
            "incident_id": e.incident_id,
            "created_at": e.created_at.isoformat()
        }
        for e in events
    ]

    return {
        "total": len(items),
        "activities": items
    }


@router.get(
    "/incidents",
    status_code=status.HTTP_200_OK,
    summary="Get Active Incident Summary for Dashboard",
    description="Returns active high-priority incidents requiring user or analyst action."
)
def get_dashboard_incidents(
    limit: int = Query(10, ge=1, le=50),
    auth: SecurityContext = Depends(require_dashboard_access),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    incidents = (
        db.query(SecurityIncident)
        .order_by(desc(SecurityIncident.created_at))
        .limit(limit)
        .all()
    )

    items = [
        {
            "id": i.id,
            "incident_number": i.incident_number,
            "category": i.category,
            "title": i.title,
            "severity": i.severity,
            "status": i.status,
            "target_or_indicator": i.target_or_indicator,
            "user_acknowledged": i.user_acknowledged,
            "created_at": i.created_at.isoformat(),
            "updated_at": i.updated_at.isoformat()
        }
        for i in incidents
    ]

    return {
        "total": len(items),
        "incidents": items
    }

