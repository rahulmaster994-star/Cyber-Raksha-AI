"""
Cyber Raksha AI - Private Security Operations Center (SOC) Admin API Routes
Stage 9/10: Private Admin Control Room
Provides comprehensive administrator operations, telemetry, device controls,
user directory, global event monitoring, incident lifecycle, threat intelligence,
model monitoring, and audit logging.
"""
import hmac
import json
import time
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, status
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import desc, func, or_

from app.core.config import settings
from app.core.feature_flags import feature_flags
from app.core.alert_manager import alert_manager
from app.core.observability import metrics_tracker, get_detailed_health_status
from app.core.job_manager import job_manager
from app.core.auth_utils import create_access_token, verify_access_token, verify_password
from app.services.model_monitor import model_monitor
from app.services.threat_intel_ops import threat_intel_ops
from app.services.notification_service import notification_service
from app.database.session import get_db

from app.models.user import User
from app.models.device import Device
from app.models.security_event import SecurityEvent
from app.models.incident import SecurityIncident, IncidentAction
from app.models.threat_intel import ThreatIndicator, ThreatFeedLog
from app.models.feedback import AnalysisFeedback
from app.models.admin_audit import AdminAuditLog
from app.models.phone_reputation import PhoneReputation

router = APIRouter(tags=["Private Admin SOC Operations"])


# ---------------------------------------------------------------------------
# Strict Administrator Authentication Dependency
# ---------------------------------------------------------------------------

class AdminAuthContext:
    def __init__(self, admin_id: str, auth_method: str):
        self.admin_id = admin_id
        self.auth_method = auth_method  # "TOKEN" or "KEY"


def require_admin_access(
    request: Request,
    x_admin_key: Optional[str] = Header(None, alias="x-admin-key"),
    db: Session = Depends(get_db)
) -> AdminAuthContext:
    """
    Enforces strict administrator authentication.
    Accepts:
    1. X-Admin-Key header validated via constant-time comparison (Master Secret Key).
    2. X-Admin-Key header containing a verified Admin JWT token.
    3. Authorization: Bearer <token> where token is a verified Admin JWT.
    Fails closed with HTTP 401 Unauthorized if missing, forged, or invalid.
    """
    # 1. Check X-Admin-Key header
    if x_admin_key:
        clean_key = x_admin_key.strip()
        if settings.ADMIN_SECRET_KEY and hmac.compare_digest(clean_key, settings.ADMIN_SECRET_KEY):
            return AdminAuthContext(admin_id="master_admin", auth_method="KEY")
        # Check if X-Admin-Key is a valid Admin JWT token
        token_payload = verify_access_token(clean_key)
        if token_payload and token_payload.get("role") in ("admin", "superadmin"):
            return AdminAuthContext(
                admin_id=str(token_payload.get("username") or token_payload.get("sub") or "admin"),
                auth_method="TOKEN"
            )

    # 2. Check Authorization Bearer JWT Token
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header[7:].strip()
        payload = verify_access_token(token)
        if payload and payload.get("role") in ("admin", "superadmin"):
            return AdminAuthContext(
                admin_id=str(payload.get("username") or payload.get("sub") or "admin"),
                auth_method="TOKEN"
            )

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Unauthorized: Administrator authentication required. Provide valid X-Admin-Key or Admin Bearer Token."
    )


# ---------------------------------------------------------------------------
# Request / Response Schemas
# ---------------------------------------------------------------------------

class AdminLoginRequest(BaseModel):
    admin_key: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None


class FeatureFlagUpdate(BaseModel):
    enabled: bool


class UserStatusUpdate(BaseModel):
    is_active: bool


class IncidentCreateRequest(BaseModel):
    category: str = Field(..., max_length=100)
    title: str = Field(..., max_length=255)
    severity: str = Field("HIGH", max_length=50)
    summary: str
    target_or_indicator: Optional[str] = None
    device_id: Optional[str] = None


class IncidentUpdateRequest(BaseModel):
    status: Optional[str] = Field(None, max_length=50)
    resolution_notes: Optional[str] = None
    user_acknowledged: Optional[bool] = None


class ThreatIndicatorCreate(BaseModel):
    indicator_type: str = Field(..., max_length=50)  # URL, DOMAIN, IP, PHONE, HASH
    indicator_value: str = Field(..., max_length=255)
    threat_type: str = Field("MALICIOUS", max_length=100)
    source_name: str = Field("ADMIN_MANUAL", max_length=100)
    confidence: float = Field(0.95, ge=0.0, le=1.0)


class ReviewUpdateRequest(BaseModel):
    review_status: str = Field(..., description="UNDER_REVIEW | CONFIRMED | REJECTED | INCONCLUSIVE")
    reviewer_notes: Optional[str] = Field(None, max_length=2000)
    reviewed_by: Optional[str] = Field(None, max_length=100)
    model_config = {"str_strip_whitespace": True}


# ---------------------------------------------------------------------------
# Section 0: Administrator Authentication Routes
# ---------------------------------------------------------------------------

@router.post(
    "/admin/auth/login",
    status_code=status.HTTP_200_OK,
    summary="Admin Control Room Authentication",
    description="Authenticates platform administrator using master key or admin credentials. Returns short-lived session token."
)
def admin_login(
    payload: AdminLoginRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    ip = request.client.host if request.client else "unknown"

    # Authenticate via master key
    if payload.admin_key and settings.ADMIN_SECRET_KEY:
        if hmac.compare_digest(payload.admin_key.strip(), settings.ADMIN_SECRET_KEY):
            token = create_access_token(
                {"sub": "master_admin", "username": "admin", "role": "admin", "is_admin": True},
                expires_minutes=240
            )
            # Record audit log
            db.add(AdminAuditLog(
                admin_identifier="master_admin",
                action="ADMIN_LOGIN_SUCCESS",
                target_type="SYSTEM",
                details=json.dumps({"method": "KEY", "ip": ip}),
                ip_address=ip
            ))
            db.commit()
            return {
                "access_token": token,
                "token_type": "bearer",
                "role": "admin",
                "expires_in_seconds": 14400,
                "message": "Administrator authenticated successfully."
            }

    # Authenticate via database admin username + password
    if payload.username and payload.password:
        user = db.query(User).filter(
            User.username == payload.username.strip(),
            User.role.in_(["admin", "superadmin"]),
            User.is_active == True
        ).first()
        if user and verify_password(payload.password, user.hashed_password):
            token = create_access_token(
                {"sub": str(user.id), "username": user.username, "role": user.role, "is_admin": True},
                expires_minutes=240
            )
            db.add(AdminAuditLog(
                admin_identifier=user.username,
                action="ADMIN_LOGIN_SUCCESS",
                target_type="USER",
                target_id=str(user.id),
                details=json.dumps({"method": "CREDENTIALS", "ip": ip}),
                ip_address=ip
            ))
            db.commit()
            return {
                "access_token": token,
                "token_type": "bearer",
                "role": user.role,
                "expires_in_seconds": 14400,
                "message": "Administrator authenticated successfully."
            }

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid administrator credentials or secret key."
    )


@router.get(
    "/admin/auth/verify",
    status_code=status.HTTP_200_OK,
    summary="Verify Admin Session",
    description="Validates current administrator session status."
)
def admin_verify(auth: AdminAuthContext = Depends(require_admin_access)):
    return {
        "status": "AUTHENTICATED",
        "admin_id": auth.admin_id,
        "auth_method": auth.auth_method,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


# ---------------------------------------------------------------------------
# Section A: Live System Overview
# ---------------------------------------------------------------------------

@router.get(
    "/admin/overview",
    status_code=status.HTTP_200_OK,
    summary="Admin System Overview",
    description="Complete real-time platform overview queried directly from backend database."
)
def admin_overview(
    auth: AdminAuthContext = Depends(require_admin_access),
    db: Session = Depends(get_db)
):
    now = datetime.now(timezone.utc)
    today_start = datetime(now.year, now.month, now.day, tzinfo=timezone.utc)

    # 1. User Statistics
    total_users = db.query(User).count()
    active_users = db.query(User).filter(User.is_active == True).count()

    # 2. Device Statistics
    total_devices = db.query(Device).count()
    active_cutoff = now - timedelta(hours=24)
    active_devices = db.query(Device).filter(Device.last_seen_at >= active_cutoff, Device.is_revoked == False).count()
    inactive_devices = db.query(Device).filter(Device.last_seen_at < active_cutoff, Device.is_revoked == False).count()
    revoked_devices = db.query(Device).filter(Device.is_revoked == True).count()

    # 3. Security Event Statistics
    total_events = db.query(SecurityEvent).count()
    events_today = db.query(SecurityEvent).filter(SecurityEvent.created_at >= today_start).count()
    critical_events = db.query(SecurityEvent).filter(SecurityEvent.severity == "CRITICAL").count()
    high_events = db.query(SecurityEvent).filter(SecurityEvent.severity == "HIGH").count()

    events_by_component = dict(
        db.query(SecurityEvent.source_component, func.count(SecurityEvent.id))
        .group_by(SecurityEvent.source_component)
        .all()
    )

    # 4. Incident Statistics
    total_incidents = db.query(SecurityIncident).count()
    active_incidents = db.query(SecurityIncident).filter(
        SecurityIncident.status.notin_(["RESOLVED", "CLOSED", "FALSE_POSITIVE"])
    ).count()
    critical_incidents = db.query(SecurityIncident).filter(
        SecurityIncident.severity == "CRITICAL",
        SecurityIncident.status.notin_(["RESOLVED", "CLOSED", "FALSE_POSITIVE"])
    ).count()
    pending_investigations = db.query(SecurityIncident).filter(
        SecurityIncident.status.in_(["NEW", "INVESTIGATING", "ACTION_REQUIRED"])
    ).count()
    resolved_incidents = db.query(SecurityIncident).filter(
        SecurityIncident.status.in_(["RESOLVED", "CLOSED"])
    ).count()

    # 5. Threat Intelligence
    total_threat_indicators = db.query(ThreatIndicator).count()
    active_threat_indicators = db.query(ThreatIndicator).filter(ThreatIndicator.is_active == True).count()
    total_phone_reputations = db.query(PhoneReputation).count()
    last_feed = db.query(ThreatFeedLog).order_by(desc(ThreatFeedLog.fetched_at)).first()

    # 6. Observability & Subsystem Health
    health = get_detailed_health_status()
    metrics = metrics_tracker.get_metrics_summary()
    alerts_summary = alert_manager.get_summary()

    return {
        "platform": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.APP_ENV,
        "timestamp": now.isoformat(),
        "health_status": health["status"],
        "overall_health": health["status"],
        "subsystems": health["services"],
        "users": {
            "total": total_users,
            "active": active_users
        },
        "devices": {
            "total_registered": total_devices,
            "active": active_devices,
            "inactive": inactive_devices,
            "revoked": revoked_devices
        },
        "events": {
            "total": total_events,
            "today": events_today,
            "critical": critical_events,
            "high": high_events,
            "by_component": events_by_component
        },
        "incidents": {
            "total": total_incidents,
            "active": active_incidents,
            "critical": critical_incidents,
            "pending_investigation": pending_investigations,
            "resolved": resolved_incidents
        },
        "threat_intelligence": {
            "total_indicators": total_threat_indicators,
            "active_indicators": active_threat_indicators,
            "phone_reputation_entries": total_phone_reputations,
            "last_sync": last_feed.fetched_at.isoformat() if last_feed else None
        },
        "performance": {
            "total_requests": metrics["total_requests"],
            "error_rate_percent": metrics["error_rate_percent"],
            "uptime_seconds": metrics["uptime_seconds"]
        },
        "alerts": alerts_summary,
        "ai_models": model_monitor.get_models_overview(),
        "feature_flags": feature_flags.get_all_flags()
    }


# ---------------------------------------------------------------------------
# Section B: User Directory
# ---------------------------------------------------------------------------

@router.get(
    "/admin/users",
    status_code=status.HTTP_200_OK,
    summary="Admin User Directory",
    description="Lists registered platform accounts with search, role filter, pagination, and privacy masking."
)
def admin_list_users(
    search: Optional[str] = Query(None, description="Search by username or email"),
    role: Optional[str] = Query(None, description="Filter by role: citizen, analyst, admin"),
    is_active: Optional[bool] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    auth: AdminAuthContext = Depends(require_admin_access),
    db: Session = Depends(get_db)
):
    query = db.query(User)
    if search:
        s = f"%{search.strip().lower()}%"
        query = query.filter(or_(User.username.ilike(s), User.email.ilike(s)))
    if role:
        query = query.filter(User.role == role.lower())
    if is_active is not None:
        query = query.filter(User.is_active == is_active)

    total = query.count()
    offset = (page - 1) * limit
    users = query.order_by(desc(User.created_at)).offset(offset).limit(limit).all()

    items = []
    for u in users:
        # Mask sensitive PII
        email_parts = u.email.split("@")
        masked_email = f"{email_parts[0][:2]}***@{email_parts[1]}" if len(email_parts) == 2 else u.email
        masked_mobile = f"{u.mobile_number[:4]}****{u.mobile_number[-2:]}" if u.mobile_number and len(u.mobile_number) >= 8 else u.mobile_number

        items.append({
            "id": u.id,
            "username": u.username,
            "email_masked": masked_email,
            "mobile_masked": masked_mobile,
            "role": u.role,
            "is_active": u.is_active,
            "is_email_verified": u.is_email_verified,
            "is_mobile_verified": u.is_mobile_verified,
            "consent_given": u.consent_given,
            "created_at": u.created_at.isoformat(),
            "updated_at": u.updated_at.isoformat()
        })

    return {
        "total": total,
        "page": page,
        "limit": limit,
        "users": items
    }


@router.patch(
    "/admin/users/{user_id}/status",
    status_code=status.HTTP_200_OK,
    summary="Update User Account Status",
    description="Activates or deactivates a user account. Records administrative audit log."
)
def admin_update_user_status(
    user_id: int,
    payload: UserStatusUpdate,
    request: Request,
    auth: AdminAuthContext = Depends(require_admin_access),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User ID {user_id} not found.")

    user.is_active = payload.is_active
    user.updated_at = datetime.now(timezone.utc)

    # Record Audit Log
    db.add(AdminAuditLog(
        admin_identifier=auth.admin_id,
        action="USER_STATUS_UPDATED",
        target_type="USER",
        target_id=str(user.id),
        details=json.dumps({"is_active": payload.is_active, "username": user.username}),
        ip_address=request.client.host if request.client else None
    ))
    db.commit()

    return {
        "user_id": user.id,
        "username": user.username,
        "is_active": user.is_active,
        "message": f"User account has been {'activated' if user.is_active else 'deactivated'}."
    }


# ---------------------------------------------------------------------------
# Section C: Device Management
# ---------------------------------------------------------------------------

@router.get(
    "/admin/devices",
    status_code=status.HTTP_200_OK,
    summary="Admin Device Management Directory",
    description="Lists registered mobile and client devices with posture, version, and threat event metrics."
)
def admin_list_devices(
    search: Optional[str] = Query(None, description="Search by device_id or device_name"),
    status_filter: Optional[str] = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    auth: AdminAuthContext = Depends(require_admin_access),
    db: Session = Depends(get_db)
):
    query = db.query(Device)
    if search:
        s = f"%{search.strip()}%"
        query = query.filter(or_(Device.device_id.ilike(s), Device.device_name.ilike(s)))
    if status_filter:
        query = query.filter(Device.status == status_filter.upper())

    total = query.count()
    offset = (page - 1) * limit
    devices = query.order_by(desc(Device.last_seen_at)).offset(offset).limit(limit).all()

    items = []
    for d in devices:
        event_count = db.query(SecurityEvent).filter(SecurityEvent.device_id == d.device_id).count()
        last_ev = (
            db.query(SecurityEvent)
            .filter(SecurityEvent.device_id == d.device_id)
            .order_by(desc(SecurityEvent.created_at))
            .first()
        )
        items.append({
            "id": d.id,
            "device_id": d.device_id,
            "device_name": d.device_name,
            "app_version": d.app_version,
            "status": d.status,
            "security_posture": d.security_posture,
            "is_revoked": d.is_revoked,
            "registered_at": d.registered_at.isoformat(),
            "last_seen_at": d.last_seen_at.isoformat(),
            "event_count": event_count,
            "last_event_type": last_ev.event_type if last_ev else None,
            "last_event_time": last_ev.created_at.isoformat() if last_ev else None
        })

    return {
        "total": total,
        "page": page,
        "limit": limit,
        "devices": items
    }


@router.post(
    "/admin/devices/{device_id}/revoke",
    status_code=status.HTTP_200_OK,
    summary="Revoke Device Credentials (Admin)",
    description="Revokes device authentication and blocks access. Audited."
)
def admin_revoke_device(
    device_id: str,
    request: Request,
    auth: AdminAuthContext = Depends(require_admin_access),
    db: Session = Depends(get_db)
):
    device = db.query(Device).filter(Device.device_id == device_id).first()
    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Device '{device_id}' not found.")

    device.status = "REVOKED"
    device.is_revoked = True
    device.device_token_hash = None
    device.security_posture = "REVOKED"

    db.add(AdminAuditLog(
        admin_identifier=auth.admin_id,
        action="DEVICE_REVOKED",
        target_type="DEVICE",
        target_id=device_id,
        details=json.dumps({"device_name": device.device_name}),
        ip_address=request.client.host if request.client else None
    ))
    db.commit()

    return {
        "device_id": device_id,
        "status": "REVOKED",
        "message": f"Device '{device_id}' credentials revoked successfully."
    }


@router.post(
    "/admin/devices/{device_id}/suspend",
    status_code=status.HTTP_200_OK,
    summary="Suspend Device Access (Admin)",
    description="Temporarily suspends device synchronization. Audited."
)
def admin_suspend_device(
    device_id: str,
    request: Request,
    auth: AdminAuthContext = Depends(require_admin_access),
    db: Session = Depends(get_db)
):
    device = db.query(Device).filter(Device.device_id == device_id).first()
    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Device '{device_id}' not found.")

    device.status = "SUSPENDED"
    device.security_posture = "AT_RISK"

    db.add(AdminAuditLog(
        admin_identifier=auth.admin_id,
        action="DEVICE_SUSPENDED",
        target_type="DEVICE",
        target_id=device_id,
        details=json.dumps({"device_name": device.device_name}),
        ip_address=request.client.host if request.client else None
    ))
    db.commit()

    return {
        "device_id": device_id,
        "status": "SUSPENDED",
        "message": f"Device '{device_id}' has been suspended."
    }


@router.get(
    "/admin/devices/{device_id}/activity",
    status_code=status.HTTP_200_OK,
    summary="Admin Device Activity Inspection",
    description="Returns security events and telemetry for a specific device."
)
def admin_get_device_activity(
    device_id: str,
    limit: int = Query(50, ge=1, le=100),
    auth: AdminAuthContext = Depends(require_admin_access),
    db: Session = Depends(get_db)
):
    device = db.query(Device).filter(Device.device_id == device_id).first()
    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Device '{device_id}' not found.")

    events = (
        db.query(SecurityEvent)
        .filter(SecurityEvent.device_id == device_id)
        .order_by(desc(SecurityEvent.created_at))
        .limit(limit)
        .all()
    )

    return {
        "device_id": device_id,
        "device_name": device.device_name,
        "total_events": len(events),
        "events": [
            {
                "id": ev.id,
                "event_id": ev.event_id,
                "event_type": ev.event_type,
                "severity": ev.severity,
                "source_component": ev.source_component,
                "threat_indicator": ev.threat_indicator,
                "risk_score": ev.risk_score,
                "detection_reason": ev.detection_reason,
                "description": ev.description,
                "created_at": ev.created_at.isoformat()
            }
            for ev in events
        ]
    }


# ---------------------------------------------------------------------------
# Section D: Global Security Event Monitor
# ---------------------------------------------------------------------------

@router.get(
    "/admin/security-events",
    status_code=status.HTTP_200_OK,
    summary="Global Security Event Monitor",
    description="Cross-platform unified security event feed with comprehensive search, multi-factor filters, and pagination."
)
def admin_list_security_events(
    search: Optional[str] = Query(None, description="Search indicator or description"),
    severity: Optional[str] = Query(None, description="INFO, LOW, MEDIUM, HIGH, CRITICAL"),
    source_component: Optional[str] = Query(None, description="ANDROID_APP, BROWSER_EXTENSION, CENTRAL_RISK_ENGINE"),
    device_id: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    auth: AdminAuthContext = Depends(require_admin_access),
    db: Session = Depends(get_db)
):
    query = db.query(SecurityEvent)

    if search:
        s = f"%{search.strip()}%"
        query = query.filter(or_(
            SecurityEvent.threat_indicator.ilike(s),
            SecurityEvent.description.ilike(s),
            SecurityEvent.detection_reason.ilike(s)
        ))
    if severity:
        query = query.filter(SecurityEvent.severity == severity.upper())
    if source_component:
        query = query.filter(SecurityEvent.source_component == source_component.upper())
    if device_id:
        query = query.filter(SecurityEvent.device_id == device_id)

    total = query.count()
    offset = (page - 1) * limit
    events = query.order_by(desc(SecurityEvent.created_at)).offset(offset).limit(limit).all()

    return {
        "total": total,
        "page": page,
        "limit": limit,
        "events": [
            {
                "id": e.id,
                "event_id": e.event_id,
                "event_type": e.event_type,
                "severity": e.severity,
                "source_component": e.source_component,
                "device_id": e.device_id,
                "threat_indicator": e.threat_indicator,
                "risk_score": e.risk_score,
                "detection_reason": e.detection_reason,
                "description": e.description,
                "verification_status": e.verification_status,
                "processing_status": e.processing_status,
                "incident_id": e.incident_id,
                "is_resolved": e.is_resolved,
                "created_at": e.created_at.isoformat()
            }
            for e in events
        ]
    }


@router.get(
    "/admin/security-events/{event_id}",
    status_code=status.HTTP_200_OK,
    summary="Get Detailed Security Event",
    description="Retrieves full telemetry, raw payload, and incident linkage for a single event."
)
def admin_get_security_event_detail(
    event_id: str,
    auth: AdminAuthContext = Depends(require_admin_access),
    db: Session = Depends(get_db)
):
    event = db.query(SecurityEvent).filter(
        or_(SecurityEvent.event_id == event_id, SecurityEvent.id == int(event_id) if event_id.isdigit() else False)
    ).first()

    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Security event '{event_id}' not found.")

    return {
        "id": event.id,
        "event_id": event.event_id,
        "event_type": event.event_type,
        "severity": event.severity,
        "source_component": event.source_component,
        "device_id": event.device_id,
        "threat_indicator": event.threat_indicator,
        "risk_score": event.risk_score,
        "detection_reason": event.detection_reason,
        "source_ip": event.source_ip,
        "description": event.description,
        "raw_payload": event.raw_payload,
        "verification_status": event.verification_status,
        "processing_status": event.processing_status,
        "incident_id": event.incident_id,
        "is_resolved": event.is_resolved,
        "created_at": event.created_at.isoformat()
    }


# ---------------------------------------------------------------------------
# Section F: Incident Management
# ---------------------------------------------------------------------------

@router.get(
    "/admin/incidents",
    status_code=status.HTTP_200_OK,
    summary="Admin Incident Management Directory",
    description="Lists all security incidents with search, status and severity filtering."
)
def admin_list_incidents(
    search: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    auth: AdminAuthContext = Depends(require_admin_access),
    db: Session = Depends(get_db)
):
    query = db.query(SecurityIncident)
    if search:
        s = f"%{search.strip()}%"
        query = query.filter(or_(
            SecurityIncident.incident_number.ilike(s),
            SecurityIncident.title.ilike(s),
            SecurityIncident.target_or_indicator.ilike(s)
        ))
    if severity:
        query = query.filter(SecurityIncident.severity == severity.upper())
    if status_filter:
        query = query.filter(SecurityIncident.status == status_filter.upper())

    total = query.count()
    offset = (page - 1) * limit
    incidents = query.order_by(desc(SecurityIncident.created_at)).offset(offset).limit(limit).all()

    return {
        "total": total,
        "page": page,
        "limit": limit,
        "incidents": [
            {
                "id": inc.id,
                "incident_number": inc.incident_number,
                "category": inc.category,
                "title": inc.title,
                "severity": inc.severity,
                "status": inc.status,
                "summary": inc.summary,
                "target_or_indicator": inc.target_or_indicator,
                "device_id": inc.device_id,
                "user_acknowledged": inc.user_acknowledged,
                "is_false_positive": inc.is_false_positive,
                "resolution_notes": inc.resolution_notes,
                "resolved_at": inc.resolved_at.isoformat() if inc.resolved_at else None,
                "created_at": inc.created_at.isoformat(),
                "updated_at": inc.updated_at.isoformat()
            }
            for inc in incidents
        ]
    }


@router.post(
    "/admin/incidents",
    status_code=status.HTTP_201_CREATED,
    summary="Create Security Incident Manually",
    description="Allows administrator to create a tracked security incident."
)
def admin_create_incident(
    payload: IncidentCreateRequest,
    request: Request,
    auth: AdminAuthContext = Depends(require_admin_access),
    db: Session = Depends(get_db)
):
    now = datetime.now(timezone.utc)
    incident_count = db.query(SecurityIncident).count() + 1
    inc_num = f"CR-INC-{now.year}-{incident_count:04d}"

    incident = SecurityIncident(
        incident_number=inc_num,
        category=payload.category.upper(),
        title=payload.title,
        severity=payload.severity.upper(),
        status="NEW",
        summary=payload.summary,
        target_or_indicator=payload.target_or_indicator,
        device_id=payload.device_id,
        source_components=json.dumps(["ADMIN_SOC"]),
        created_at=now,
        updated_at=now
    )
    db.add(incident)

    db.add(AdminAuditLog(
        admin_identifier=auth.admin_id,
        action="INCIDENT_CREATED",
        target_type="INCIDENT",
        target_id=inc_num,
        details=json.dumps({"title": payload.title, "severity": payload.severity}),
        ip_address=request.client.host if request.client else None
    ))
    db.commit()
    db.refresh(incident)

    return {
        "id": incident.id,
        "incident_number": incident.incident_number,
        "title": incident.title,
        "status": incident.status,
        "message": "Incident created successfully."
    }


@router.patch(
    "/admin/incidents/{incident_id}",
    status_code=status.HTTP_200_OK,
    summary="Update Incident Status & Resolution",
    description="Updates status, resolution notes, or false positive flag on an incident."
)
def admin_update_incident(
    incident_id: int,
    payload: IncidentUpdateRequest,
    request: Request,
    auth: AdminAuthContext = Depends(require_admin_access),
    db: Session = Depends(get_db)
):
    incident = db.query(SecurityIncident).filter(SecurityIncident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Incident ID {incident_id} not found.")

    now = datetime.now(timezone.utc)
    if payload.status:
        incident.status = payload.status.upper()
        if incident.status in ("RESOLVED", "CLOSED"):
            incident.resolved_at = now
        if incident.status == "FALSE_POSITIVE":
            incident.is_false_positive = True
            incident.resolved_at = now

    if payload.resolution_notes is not None:
        incident.resolution_notes = payload.resolution_notes

    if payload.user_acknowledged is not None:
        incident.user_acknowledged = payload.user_acknowledged
        incident.acknowledged_at = now

    incident.updated_at = now

    db.add(AdminAuditLog(
        admin_identifier=auth.admin_id,
        action="INCIDENT_UPDATED",
        target_type="INCIDENT",
        target_id=incident.incident_number,
        details=json.dumps({"new_status": incident.status, "notes": incident.resolution_notes}),
        ip_address=request.client.host if request.client else None
    ))
    db.commit()

    return {
        "id": incident.id,
        "incident_number": incident.incident_number,
        "status": incident.status,
        "resolution_notes": incident.resolution_notes,
        "resolved_at": incident.resolved_at.isoformat() if incident.resolved_at else None,
        "message": "Incident updated successfully."
    }


# ---------------------------------------------------------------------------
# Section G: Threat Intelligence Management
# ---------------------------------------------------------------------------

@router.get(
    "/admin/threat-intelligence",
    status_code=status.HTTP_200_OK,
    summary="Admin Threat Intelligence Overview",
    description="Returns aggregate IoC statistics, latest verified threats, and feed health."
)
def admin_get_threat_intel(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    auth: AdminAuthContext = Depends(require_admin_access),
    db: Session = Depends(get_db)
):
    total = db.query(ThreatIndicator).count()
    active_count = db.query(ThreatIndicator).filter(ThreatIndicator.is_active == True).count()
    offset = (page - 1) * limit

    indicators = (
        db.query(ThreatIndicator)
        .order_by(desc(ThreatIndicator.created_at))
        .offset(offset)
        .limit(limit)
        .all()
    )

    feed_report = threat_intel_ops.get_feed_health_report()

    return {
        "total_indicators": total,
        "active_indicators": active_count,
        "feed_health": feed_report,
        "page": page,
        "limit": limit,
        "indicators": [
            {
                "id": ind.id,
                "type": ind.indicator_type,
                "value": ind.indicator_value,
                "threat_type": ind.threat_type,
                "source": ind.source_name,
                "confidence": ind.confidence_score,
                "is_active": ind.is_active,
                "created_at": ind.created_at.isoformat() if ind.created_at else None
            }
            for ind in indicators
        ]
    }


@router.post(
    "/admin/threat-intelligence/indicators",
    status_code=status.HTTP_201_CREATED,
    summary="Add Verified Threat Indicator",
    description="Manually ingests an IoC into the platform's active threat defense repository."
)
def admin_add_threat_indicator(
    payload: ThreatIndicatorCreate,
    request: Request,
    auth: AdminAuthContext = Depends(require_admin_access),
    db: Session = Depends(get_db)
):
    now = datetime.now(timezone.utc)
    clean_val = payload.indicator_value.strip().lower()

    existing = db.query(ThreatIndicator).filter(
        ThreatIndicator.indicator_value == clean_val
    ).first()

    if existing:
        existing.is_active = True
        existing.confidence_score = payload.confidence
        existing.threat_type = payload.threat_type.upper()
        existing.source_name = payload.source_name
        existing.last_seen = now
        db.commit()
        return {"id": existing.id, "value": clean_val, "message": "Indicator updated and re-activated."}

    ind = ThreatIndicator(
        indicator_type=payload.indicator_type.upper(),
        indicator_value=clean_val,
        threat_type=payload.threat_type.upper(),
        source_name=payload.source_name,
        confidence_score=payload.confidence,
        is_active=True,
        first_seen=now,
        last_seen=now,
        created_at=now
    )
    db.add(ind)

    db.add(AdminAuditLog(
        admin_identifier=auth.admin_id,
        action="IOC_CREATED",
        target_type="IOC",
        target_id=clean_val,
        details=json.dumps({"type": payload.indicator_type, "threat_type": payload.threat_type}),
        ip_address=request.client.host if request.client else None
    ))
    db.commit()
    db.refresh(ind)

    return {
        "id": ind.id,
        "value": ind.indicator_value,
        "type": ind.indicator_type,
        "message": "Indicator successfully added to threat intelligence repository."
    }


@router.delete(
    "/admin/threat-intelligence/indicators/{indicator_id}",
    status_code=status.HTTP_200_OK,
    summary="Deactivate Threat Indicator",
    description="Deactivates an indicator so it no longer blocks traffic."
)
def admin_delete_threat_indicator(
    indicator_id: int,
    request: Request,
    auth: AdminAuthContext = Depends(require_admin_access),
    db: Session = Depends(get_db)
):
    ind = db.query(ThreatIndicator).filter(ThreatIndicator.id == indicator_id).first()
    if not ind:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Indicator ID {indicator_id} not found.")

    ind.is_active = False

    db.add(AdminAuditLog(
        admin_identifier=auth.admin_id,
        action="IOC_DEACTIVATED",
        target_type="IOC",
        target_id=ind.indicator_value,
        details=json.dumps({"id": indicator_id}),
        ip_address=request.client.host if request.client else None
    ))
    db.commit()

    return {"indicator_id": indicator_id, "is_active": False, "message": "Indicator deactivated successfully."}


# ---------------------------------------------------------------------------
# Section H: Alert Management
# ---------------------------------------------------------------------------

@router.get(
    "/admin/alerts",
    status_code=status.HTTP_200_OK,
    summary="List Operational Alerts",
    description="Returns active operational alerts requiring administrator attention."
)
def admin_list_alerts(
    limit: int = Query(50, ge=1, le=100),
    auth: AdminAuthContext = Depends(require_admin_access)
):
    return {
        "summary": alert_manager.get_summary(),
        "alerts": alert_manager.get_all_alerts(limit=limit),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@router.post(
    "/admin/alerts/{alert_id}/acknowledge",
    status_code=status.HTTP_200_OK,
    summary="Acknowledge Alert",
    description="Marks a specific operational alert as acknowledged."
)
def admin_acknowledge_alert(
    alert_id: str,
    auth: AdminAuthContext = Depends(require_admin_access)
):
    success = alert_manager.acknowledge_alert(alert_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Alert '{alert_id}' not found.")
    return {
        "alert_id": alert_id,
        "acknowledged": True,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@router.post(
    "/admin/alerts/clear",
    status_code=status.HTTP_200_OK,
    summary="Acknowledge All Alerts",
    description="Bulk acknowledges all active operational alerts."
)
def admin_clear_all_alerts(auth: AdminAuthContext = Depends(require_admin_access)):
    count = alert_manager.acknowledge_all()
    return {
        "acknowledged_count": count,
        "message": f"{count} operational alert(s) acknowledged.",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


# ---------------------------------------------------------------------------
# Section I: AI Model Monitoring
# ---------------------------------------------------------------------------

@router.get(
    "/admin/models",
    status_code=status.HTTP_200_OK,
    summary="AI Model Monitoring & Performance Telemetry",
    description="Returns real runtime health, metrics, feature sets, and latency for deployed ML models."
)
def admin_get_models_telemetry(auth: AdminAuthContext = Depends(require_admin_access)):
    models_overview = model_monitor.get_models_overview()

    return {
        "total_deployed_models": models_overview["total_deployed_models"],
        "governance": {
            "retraining_policy": "STRICT_OFFLINE_VALIDATION_ONLY",
            "auto_retraining": False
        },
        "models": models_overview.get("models", []),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@router.get(
    "/admin/model-candidates",
    status_code=status.HTTP_200_OK,
    summary="Model Candidates Governance",
    description="Returns pipeline status and governance rules for AI model evaluation."
)
@router.get("/model-candidates", include_in_schema=False)
def admin_get_model_candidates(auth: AdminAuthContext = Depends(require_admin_access)):
    return {
        "pipeline_status": "MANUAL_REVIEW_REQUIRED",
        "governance_statement": "Automatic retraining from user feedback or input drift is strictly prohibited. All candidates must undergo manual review, offline validation, and human sign-off before deployment.",
        "candidates": [],
        "retraining_policy": "OFFLINE_ONLY"
    }


# ---------------------------------------------------------------------------
# Section J: Platform Health & Deep Diagnostics
# ---------------------------------------------------------------------------

@router.get(
    "/admin/health/diagnostics",
    status_code=status.HTTP_200_OK,
    summary="Deep Platform Operational Diagnostics",
    description="Probes database latency, memory metrics, background queues, and system parameters."
)
def admin_health_diagnostics(
    auth: AdminAuthContext = Depends(require_admin_access),
    db: Session = Depends(get_db)
):
    # 1. Database Ping Latency Check
    start_t = time.perf_counter()
    try:
        db.execute(func.now())
        db_latency_ms = round((time.perf_counter() - start_t) * 1000, 2)
        db_status = "HEALTHY"
    except Exception as e:
        db_latency_ms = round((time.perf_counter() - start_t) * 1000, 2)
        db_status = f"ERROR: {str(e)}"

    detailed_health = get_detailed_health_status()
    metrics = metrics_tracker.get_metrics_summary()

    return {
        "platform_status": detailed_health["status"],
        "database": {
            "status": db_status,
            "latency_ms": db_latency_ms,
            "type": "PostgreSQL" if "postgresql" in settings.normalized_database_url else "SQLite"
        },
        "services": detailed_health["services"],
        "runtime": {
            "uptime_seconds": metrics["uptime_seconds"],
            "total_requests": metrics["total_requests"],
            "error_rate_percent": metrics["error_rate_percent"],
            "p95_latency_ms": metrics["latency_ms"]["p95"]
        },
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


# ---------------------------------------------------------------------------
# Section K: Administrative Audit Logs
# ---------------------------------------------------------------------------

@router.get(
    "/admin/audit-logs",
    status_code=status.HTTP_200_OK,
    summary="Admin Operational Audit Trail",
    description="Returns chronological audit logs of all administrative actions."
)
def admin_get_audit_logs(
    action: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    auth: AdminAuthContext = Depends(require_admin_access),
    db: Session = Depends(get_db)
):
    query = db.query(AdminAuditLog)
    if action:
        query = query.filter(AdminAuditLog.action == action.upper())

    total = query.count()
    offset = (page - 1) * limit
    logs = query.order_by(desc(AdminAuditLog.created_at)).offset(offset).limit(limit).all()

    return {
        "total": total,
        "page": page,
        "limit": limit,
        "logs": [
            {
                "id": lg.id,
                "admin": lg.admin_identifier,
                "action": lg.action,
                "target_type": lg.target_type,
                "target_id": lg.target_id,
                "details": lg.details,
                "ip_address": lg.ip_address,
                "created_at": lg.created_at.isoformat()
            }
            for lg in logs
        ]
    }


# ---------------------------------------------------------------------------
# Feature Flags & Feedback Human Review Queue (Preserved & Protected)
# ---------------------------------------------------------------------------

@router.get(
    "/admin/feature-flags",
    status_code=status.HTTP_200_OK,
    summary="List All Feature Flags",
)
def list_feature_flags(auth: AdminAuthContext = Depends(require_admin_access)):
    return {
        "feature_flags": feature_flags.get_all_flags(),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@router.patch(
    "/admin/feature-flags/{flag_name}",
    status_code=status.HTTP_200_OK,
    summary="Enable or Disable a Feature Flag",
)
def update_feature_flag(
    flag_name: str,
    payload: FeatureFlagUpdate,
    request: Request,
    auth: AdminAuthContext = Depends(require_admin_access),
    db: Session = Depends(get_db)
):
    success = feature_flags.set_flag(flag_name, payload.enabled)
    if not success:
        all_flags = list(feature_flags.get_all_flags().keys())
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"'{flag_name}' is not a registered feature flag. Valid: {all_flags}"
        )

    db.add(AdminAuditLog(
        admin_identifier=auth.admin_id,
        action="FEATURE_FLAG_UPDATED",
        target_type="SYSTEM",
        target_id=flag_name,
        details=json.dumps({"enabled": payload.enabled}),
        ip_address=request.client.host if request.client else None
    ))
    db.commit()

    return {
        "flag_name": flag_name,
        "enabled": payload.enabled,
        "message": f"Feature flag '{flag_name}' has been {'enabled' if payload.enabled else 'disabled'}.",
        "updated_at": datetime.now(timezone.utc).isoformat()
    }


@router.get(
    "/admin/feedback/pending",
    status_code=status.HTTP_200_OK,
    summary="List Pending Feedback for Human Review",
)
def list_pending_feedback(
    limit: int = Query(20, ge=1, le=100),
    auth: AdminAuthContext = Depends(require_admin_access),
    db: Session = Depends(get_db)
):
    records = (
        db.query(AnalysisFeedback)
        .filter(AnalysisFeedback.review_status == "PENDING")
        .order_by(AnalysisFeedback.created_at.asc())
        .limit(limit)
        .all()
    )

    return {
        "pending_count": len(records),
        "feedback": [
            {
                "feedback_id": r.id,
                "analysis_id": r.analysis_id,
                "target_identifier": r.target_identifier,
                "feedback_category": r.feedback_category,
                "user_explanation": r.user_explanation,
                "user_provided_label": r.user_provided_label,
                "review_status": r.review_status,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in records
        ]
    }


@router.patch(
    "/admin/feedback/{feedback_id}/review",
    status_code=status.HTTP_200_OK,
    summary="Submit Human Review Verdict on Feedback",
)
def review_feedback(
    feedback_id: int,
    payload: ReviewUpdateRequest,
    request: Request,
    auth: AdminAuthContext = Depends(require_admin_access),
    db: Session = Depends(get_db)
):
    valid_statuses = {"UNDER_REVIEW", "CONFIRMED", "REJECTED", "INCONCLUSIVE"}
    new_status = payload.review_status.upper()
    if new_status not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"'{payload.review_status}' is invalid. Allowed: {sorted(valid_statuses)}"
        )

    record = db.query(AnalysisFeedback).filter(AnalysisFeedback.id == feedback_id).first()
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Feedback ID {feedback_id} not found.")

    record.review_status = new_status
    record.reviewer_notes = payload.reviewer_notes
    record.reviewed_by = payload.reviewed_by or auth.admin_id
    record.reviewed_at = datetime.now(timezone.utc)

    db.add(AdminAuditLog(
        admin_identifier=auth.admin_id,
        action="FEEDBACK_REVIEWED",
        target_type="FEEDBACK",
        target_id=str(feedback_id),
        details=json.dumps({"status": new_status, "reviewer": record.reviewed_by}),
        ip_address=request.client.host if request.client else None
    ))
    db.commit()

    return {
        "feedback_id": record.id,
        "new_review_status": record.review_status,
        "reviewed_by": record.reviewed_by,
        "message": "Feedback verdict recorded in audit trail."
    }


# ---------------------------------------------------------------------------
# Section E: Real-Time Admin Event Stream (SSE)
# ---------------------------------------------------------------------------

@router.get(
    "/admin/stream",
    summary="Real-Time Admin SOC Event Stream (SSE)",
    description="Live Server-Sent Events stream delivering real-time security events, alerts, and counter ticks for the Admin SOC."
)
async def admin_event_stream(
    ticket: Optional[str] = Query(None, description="Connection ticket for web EventSource"),
    x_admin_key: Optional[str] = Header(None, alias="x-admin-key"),
    request: Request = None,
    db: Session = Depends(get_db)
):
    # Authenticate via ticket, header, or query
    is_authenticated = False
    if x_admin_key and settings.ADMIN_SECRET_KEY and hmac.compare_digest(x_admin_key.strip(), settings.ADMIN_SECRET_KEY):
        is_authenticated = True
    elif ticket:
        from app.services.ticket_service import ticket_service
        ticket_data = ticket_service.consume_ticket(ticket)
        if ticket_data and ticket_data.is_admin:
            is_authenticated = True
    elif request:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            payload = verify_access_token(auth_header[7:].strip())
            if payload and payload.get("role") in ("admin", "superadmin"):
                is_authenticated = True

    if not is_authenticated:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Administrator authentication required to subscribe to live SOC stream."
        )

    return StreamingResponse(
        notification_service.stream_notifications(
            client_device_id=None,
            is_admin=True
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )
