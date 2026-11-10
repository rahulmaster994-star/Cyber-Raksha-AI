"""
Cyber Raksha AI - Mobile Device API Routes
Phase B1: Native Android Foundation
"""
import json
import secrets
import hashlib
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.database.session import get_db
from app.models.device import Device
from app.models.security_event import SecurityEvent
from app.core.security import get_security_context, SecurityContext
from app.schemas.device import (
    DeviceRegisterRequest,
    DeviceRegistrationResponse,
    DeviceStatusResponse,
    ProtectionModulesStatus,
    DeviceActivityListResponse,
    DeviceActivityItem
)

router = APIRouter(prefix="/devices", tags=["Mobile Devices & Android Foundation"])


@router.post(
    "/register",
    response_model=DeviceRegistrationResponse,
    status_code=status.HTTP_200_OK,
    summary="Register Mobile Device",
    description="Registers or synchronizes an Android device using an application-generated UUID or installation token."
)
def register_device(payload: DeviceRegisterRequest, db: Session = Depends(get_db)):
    now = datetime.now(timezone.utc)
    device = db.query(Device).filter(Device.device_id == payload.device_id).first()
    default_modules = ProtectionModulesStatus().model_dump()

    # Generate secure 256-bit device token
    device_token = secrets.token_hex(32)
    token_hash = hashlib.sha256(device_token.encode()).hexdigest()

    if not device:
        device = Device(
            device_id=payload.device_id,
            device_name=payload.device_name,
            app_version=payload.app_version,
            status="ACTIVE",
            security_posture="PROTECTED",
            device_token_hash=token_hash,
            is_revoked=False,
            registered_at=now,
            last_seen_at=now,
            protection_modules=json.dumps(default_modules)
        )
        db.add(device)
    else:
        device.device_name = payload.device_name
        device.app_version = payload.app_version
        device.last_seen_at = now
        device.status = "ACTIVE"
        device.is_revoked = False
        device.device_token_hash = token_hash
        if not device.protection_modules:
            device.protection_modules = json.dumps(default_modules)

    db.commit()
    db.refresh(device)

    modules_dict = json.loads(device.protection_modules) if device.protection_modules else default_modules

    return DeviceRegistrationResponse(
        device_id=device.device_id,
        device_name=device.device_name,
        app_version=device.app_version,
        status=device.status,
        security_posture=device.security_posture,
        device_token=device_token,
        registered_at=device.registered_at,
        last_seen_at=device.last_seen_at,
        modules=ProtectionModulesStatus(**modules_dict),
        server_timestamp=now,
        message="Device registered and synchronized successfully."
    )


@router.post(
    "/{device_id}/revoke",
    status_code=status.HTTP_200_OK,
    summary="Revoke Device Credentials",
    description="Invalidates a device's authentication credentials and revokes mobile access."
)
def revoke_device(device_id: str, db: Session = Depends(get_db)):
    device = db.query(Device).filter(Device.device_id == device_id).first()
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device '{device_id}' is not registered."
        )

    device.status = "REVOKED"
    device.is_revoked = True
    device.device_token_hash = None
    device.security_posture = "REVOKED"
    db.commit()

    return {
        "device_id": device.device_id,
        "status": "REVOKED",
        "message": "Device credentials successfully revoked."
    }


@router.get(
    "/{device_id}/status",
    response_model=DeviceStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Device Status & Protection Health",
    description="Retrieves current device registration status, security posture, and module health with caller authorization."
)
def get_device_status(
    device_id: str,
    sec_ctx: SecurityContext = Depends(get_security_context),
    db: Session = Depends(get_db)
):
    # Phase B3.1: Enforce device authorization boundary
    if sec_ctx.is_authenticated and not sec_ctx.can_access_device(device_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied: Cannot access status of device '{device_id}'."
        )

    now = datetime.now(timezone.utc)
    device = db.query(Device).filter(Device.device_id == device_id).first()
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device '{device_id}' is not registered."
        )

    # Update heartbeat
    device.last_seen_at = now
    db.commit()

    default_modules = ProtectionModulesStatus().model_dump()
    modules_dict = json.loads(device.protection_modules) if device.protection_modules else default_modules

    return DeviceStatusResponse(
        device_id=device.device_id,
        device_name=device.device_name,
        app_version=device.app_version,
        status=device.status,
        security_posture=device.security_posture,
        registered_at=device.registered_at,
        last_seen_at=device.last_seen_at,
        modules=ProtectionModulesStatus(**modules_dict),
        server_timestamp=now
    )


@router.get(
    "/{device_id}/activity",
    response_model=DeviceActivityListResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Security Events & Activity Feed",
    description="Returns verified security incidents and alerts for the mobile activity feed, strictly isolated per device."
)
def get_device_activity(
    device_id: str,
    limit: int = Query(20, ge=1, le=100),
    sec_ctx: SecurityContext = Depends(get_security_context),
    db: Session = Depends(get_db)
):
    # Phase B3.1: Enforce device authorization boundary
    if sec_ctx.is_authenticated and not sec_ctx.can_access_device(device_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied: Cannot access activity feed of device '{device_id}'."
        )

    device = db.query(Device).filter(Device.device_id == device_id).first()
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device '{device_id}' is not registered."
        )

    # Strict isolation: return only events belonging to this device or global system alerts
    events = (
        db.query(SecurityEvent)
        .filter((SecurityEvent.device_id == device_id) | (SecurityEvent.device_id.is_(None)))
        .order_by(desc(SecurityEvent.created_at))
        .limit(limit)
        .all()
    )

    items = [
        DeviceActivityItem(
            id=ev.id,
            event_type=ev.event_type,
            severity=ev.severity,
            description=ev.description,
            source_component=ev.source_component,
            created_at=ev.created_at
        )
        for ev in events
    ]

    return DeviceActivityListResponse(
        device_id=device.device_id,
        total_events=len(items),
        events=items
    )
