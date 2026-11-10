"""
Cyber Raksha AI - Hardened Mobile Fraud Protection API Routes
Phase B2 & B2.1: Intelligent SMS & Call Fraud Protection & Security Hardening
"""
import hashlib
import hmac
import json
import time
from collections import defaultdict
from datetime import datetime, timezone
from typing import Optional, Dict, List
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.database.session import get_db
from app.models.device import Device
from app.models.sms_analysis import SmsAnalysis
from app.models.phone_reputation import PhoneReputation
from app.models.threat_intel import ThreatIndicator
from app.schemas.mobile import (
    MessageAnalysisRequest,
    MessageAnalysisResponse,
    NumberCheckRequest,
    NumberCheckResponse,
    ReportThreatRequest,
    ReportThreatResponse,
    DisputeNumberRequest,
    DisputeNumberResponse,
    ThreatHistoryResponse,
    ThreatHistoryItem,
    ProtectionStatusResponse
)
from app.services.sms_analysis_service import sms_analysis_service
from app.services.phone_reputation_service import phone_reputation_service

router = APIRouter(prefix="/mobile", tags=["Mobile Fraud Protection (Phase B2 & B2.1)"])

# In-memory per-device rate limiter: device_id -> list of timestamps
_rate_limits: Dict[str, List[float]] = defaultdict(list)
RATE_LIMIT_WINDOW = 60.0  # 1 minute window
MAX_ANALYSIS_PER_WINDOW = 60
MAX_REPORTS_PER_WINDOW = 20


def _check_rate_limit(device_id: str, max_requests: int, endpoint_name: str):
    now = time.time()
    timestamps = _rate_limits[f"{device_id}:{endpoint_name}"]
    # Evict expired timestamps
    _rate_limits[f"{device_id}:{endpoint_name}"] = [t for t in timestamps if now - t < RATE_LIMIT_WINDOW]
    if len(_rate_limits[f"{device_id}:{endpoint_name}"]) >= max_requests:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded for {endpoint_name}. Please wait before making more requests."
        )
    _rate_limits[f"{device_id}:{endpoint_name}"].append(now)


def _verify_device(db: Session, device_id: str, request: Optional[Request] = None) -> Device:
    """
    Validates device registration, checks revocation state, and verifies
    cryptographic X-Device-Token authentication credentials when present.
    """
    device = db.query(Device).filter(Device.device_id == device_id).first()
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device '{device_id}' is not registered with Cyber Raksha AI."
        )

    if device.is_revoked or device.status == "REVOKED":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Device authentication credentials have been revoked."
        )

    # Cryptographic Device Token Verification
    if device.device_token_hash and request is not None:
        token = request.headers.get("X-Device-Token")
        if not token:
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header[7:].strip()

        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing device authentication credential. Provide X-Device-Token header."
            )

        token_hash = hashlib.sha256(token.strip().encode("utf-8")).hexdigest()
        if not hmac.compare_digest(token_hash, device.device_token_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid device authentication credential."
            )

    return device


@router.post(
    "/analyze-message",
    response_model=MessageAnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Analyze SMS Message for Fraud & Threat Indicators",
    description="Evaluates SMS text for banking, UPI, OTP, delivery scams, digital arrest, urgency, and malicious links without retaining plain text."
)
def analyze_message(payload: MessageAnalysisRequest, request: Request, db: Session = Depends(get_db)):
    _verify_device(db, payload.device_id, request)
    _check_rate_limit(payload.device_id, MAX_ANALYSIS_PER_WINDOW, "analyze-message")

    result = sms_analysis_service.analyze_sms(
        db=db,
        device_id=payload.device_id,
        message_text=payload.message_text,
        sender=payload.sender
    )
    return MessageAnalysisResponse(**result)


@router.post(
    "/check-number",
    response_model=NumberCheckResponse,
    status_code=status.HTTP_200_OK,
    summary="Check Phone Number Reputation & Scam History",
    description="Queries normalized caller reputation database. Accurately reports UNKNOWN for numbers with no adverse history."
)
def check_number(payload: NumberCheckRequest, request: Request, db: Session = Depends(get_db)):
    _verify_device(db, payload.device_id, request)

    result = phone_reputation_service.check_number(db, payload.phone_number)
    return NumberCheckResponse(**result)


@router.get(
    "/threat-history",
    response_model=ThreatHistoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Device Mobile Threat History",
    description="Retrieves historical SMS fraud detections strictly isolated to the requesting device."
)
def get_threat_history(
    device_id: str = Query(..., description="Device identifier for strict tenant isolation"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    threat_type: Optional[str] = Query(None, description="Optional filter by threat type"),
    request: Request = None,
    db: Session = Depends(get_db)
):
    _verify_device(db, device_id, request)

    query = (
        db.query(SmsAnalysis)
        .filter(SmsAnalysis.device_id == device_id)
        .order_by(desc(SmsAnalysis.analyzed_at))
    )

    total = query.count()
    analyses = query.offset(skip).limit(limit).all()

    items = []
    for a in analyses:
        reasons = []
        if a.detection_reasons:
            try:
                reasons = json.loads(a.detection_reasons)
            except Exception:
                reasons = [a.detection_reasons]

        items.append(
            ThreatHistoryItem(
                id=a.id,
                threat_type="SMS",
                target_or_hash=a.message_hash[:16] + "...",
                risk_level=a.risk_level,
                risk_score=a.risk_score,
                fraud_category=a.fraud_category,
                detection_reasons=reasons,
                timestamp=a.analyzed_at
            )
        )

    return ThreatHistoryResponse(
        device_id=device_id,
        total=total,
        items=items
    )


@router.get(
    "/protection-status",
    response_model=ProtectionStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Mobile Protection Capabilities & Intel Health",
    description="Returns current active fraud protection capabilities, threat signature counts, and reputation cache state."
)
def get_protection_status(
    device_id: str = Query(..., description="Registered device identifier"),
    request: Request = None,
    db: Session = Depends(get_db)
):
    device = _verify_device(db, device_id, request)

    # Count threat intel signatures & phone reputation records
    sig_count = db.query(ThreatIndicator).filter(ThreatIndicator.is_active == True).count()
    rep_count = db.query(PhoneReputation).count()

    return ProtectionStatusResponse(
        device_id=device.device_id,
        sms_protection="ACTIVE",
        call_protection="ACTIVE",
        database_signatures_count=sig_count,
        phone_reputation_entries=rep_count,
        last_sync=device.last_seen_at
    )


@router.post(
    "/report-threat",
    response_model=ReportThreatResponse,
    status_code=status.HTTP_200_OK,
    summary="Report Malicious Number or Phishing URL",
    description="Submits crowd-sourced intelligence for a fraudulent caller, SMS sender, or scam link with Sybil defense."
)
def report_threat(payload: ReportThreatRequest, request: Request, db: Session = Depends(get_db)):
    _verify_device(db, payload.device_id, request)
    _check_rate_limit(payload.device_id, MAX_REPORTS_PER_WINDOW, "report-threat")

    threat_type = payload.threat_type.upper()
    indicator_val = payload.indicator_value.strip()

    if threat_type in {"PHONE_NUMBER", "SMS_SENDER"}:
        record = phone_reputation_service.report_number(
            db=db,
            raw_number=indicator_val,
            reporting_device_id=payload.device_id,
            fraud_category=payload.fraud_category,
            notes=payload.description
        )
        return ReportThreatResponse(
            success=True,
            message=f"Phone number '{indicator_val}' reported successfully. Current risk level: {record.risk_level}.",
            indicator_value=indicator_val,
            report_id=record.id
        )
    elif threat_type == "MALICIOUS_URL":
        now = datetime.now(timezone.utc)
        indicator = (
            db.query(ThreatIndicator)
            .filter(ThreatIndicator.indicator_value == indicator_val)
            .first()
        )
        if not indicator:
            indicator = ThreatIndicator(
                indicator_type="URL",
                indicator_value=indicator_val,
                threat_type=payload.fraud_category or "PHISHING",
                severity="HIGH",
                confidence_score=0.85,
                source_name="MOBILE_COMMUNITY",
                description=payload.description or "Reported via Cyber Raksha Mobile App",
                is_active=True,
                first_seen=now,
                last_seen=now,
                created_at=now
            )
            db.add(indicator)
            db.commit()
            db.refresh(indicator)

        return ReportThreatResponse(
            success=True,
            message=f"Malicious URL '{indicator_val}' submitted to threat intelligence database.",
            indicator_value=indicator_val,
            report_id=indicator.id
        )

    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported threat_type.")


@router.post(
    "/report-threat/dispute",
    response_model=DisputeNumberResponse,
    status_code=status.HTTP_200_OK,
    summary="Dispute Caller Risk Classification",
    description="Allows users to submit a false-positive correction for a mistakenly flagged phone number."
)
def dispute_number(payload: DisputeNumberRequest, request: Request, db: Session = Depends(get_db)):
    _verify_device(db, payload.device_id, request)

    result = phone_reputation_service.dispute_number(
        db=db,
        raw_number=payload.phone_number,
        reporting_device_id=payload.device_id,
        reason=payload.reason
    )
    if not result.get("success"):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=result.get("message"))

    return DisputeNumberResponse(**result)
