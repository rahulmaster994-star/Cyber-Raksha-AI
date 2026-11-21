"""
Cyber Raksha AI - Keypad User Protection API Routes
Protects elderly citizens using traditional keypad feature phones via Guardian-Assisted Family Shield.
Provides family registration, scam intelligence, SMS/Call analysis, multilingual education, and alert management.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.user import User
from app.api.routes.auth import get_current_user
from app.schemas.keypad_protection import (
    KeypadElderlyUserCreate,
    KeypadElderlyUserResponse,
    KeypadSmsCheckRequest,
    KeypadSmsCheckResponse,
    KeypadCallCheckRequest,
    KeypadCallCheckResponse,
    KeypadScamNumberReportRequest,
    KeypadScamNumberReportResponse,
    KeypadAlertSummaryResponse,
    KeypadEducationResponse,
    KeypadOfficialHelpdeskResponse
)
from app.services.keypad_service import KeypadService

router = APIRouter(prefix="/keypad", tags=["Keypad User Protection"])


# ── 1. Family Registration ───────────────────────────────────────────────────

@router.post("/family", response_model=KeypadElderlyUserResponse, status_code=status.HTTP_201_CREATED)
def register_elderly_dependent(
    req: KeypadElderlyUserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Registers an elderly family member under the authenticated guardian's account.
    Stores device type (Nokia, Samsung, itel, Lava, Jio Bharat), preferred language, and consent.
    """
    if not req.consent_given:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Elderly family member consent is required to activate guardian protection shield."
        )

    elderly = KeypadService.register_elderly_member(
        db=db,
        guardian_user_id=current_user.id,
        full_name=req.full_name,
        mobile_number=req.mobile_number,
        relationship=req.relationship,
        device_type=req.device_type,
        preferred_language=req.preferred_language,
        consent_given=req.consent_given,
        consent_notes=req.consent_notes
    )

    return KeypadElderlyUserResponse(
        id=elderly.id,
        guardian_user_id=elderly.guardian_user_id,
        full_name=elderly.full_name,
        mobile_number=elderly.mobile_number,
        masked_mobile_number=elderly.masked_mobile_number,
        relationship=elderly.relationship,
        device_type=elderly.device_type,
        preferred_language=elderly.preferred_language,
        consent_given=elderly.consent_given,
        is_active=elderly.is_active,
        created_at=elderly.created_at
    )


@router.get("/family", response_model=List[KeypadElderlyUserResponse])
def list_elderly_dependents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lists all active elderly family members registered under the authenticated guardian."""
    members = KeypadService.get_elderly_members(db=db, guardian_user_id=current_user.id)
    return [
        KeypadElderlyUserResponse(
            id=m.id,
            guardian_user_id=m.guardian_user_id,
            full_name=m.full_name,
            mobile_number=m.mobile_number,
            masked_mobile_number=m.masked_mobile_number,
            relationship=m.relationship,
            device_type=m.device_type,
            preferred_language=m.preferred_language,
            consent_given=m.consent_given,
            is_active=m.is_active,
            created_at=m.created_at
        )
        for m in members
    ]


@router.delete("/family/{elderly_id}", status_code=status.HTTP_200_OK)
def remove_elderly_dependent(
    elderly_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Deactivates an elderly dependent record belonging to the authenticated guardian."""
    success = KeypadService.delete_elderly_member(db=db, guardian_user_id=current_user.id, elderly_user_id=elderly_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Elderly dependent record not found or does not belong to guardian."
        )
    return {"status": "success", "message": "Elderly dependent successfully removed."}


# ── 2. SMS Risk Analysis ─────────────────────────────────────────────────────

@router.post("/check-sms", response_model=KeypadSmsCheckResponse)
def check_keypad_sms(
    req: KeypadSmsCheckRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Guardian submits SMS received on an elderly user's keypad phone.
    Analyzes phishing links, fake KYC, payment/UPI requests, impersonation, urgency.
    Returns risk score, risk level, category, multilingual explanation, and recommended action.
    """
    if len(req.message.strip()) == 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="SMS message content cannot be empty."
        )

    result = KeypadService.analyze_keypad_sms(
        db=db,
        guardian_user_id=current_user.id,
        message=req.message,
        sender=req.sender,
        elderly_user_id=req.elderly_user_id,
        preferred_language=req.preferred_language or "en"
    )
    return KeypadSmsCheckResponse(**result)


# ── 3. Call Risk Check ───────────────────────────────────────────────────────

@router.post("/check-call", response_model=KeypadCallCheckResponse)
def check_keypad_call(
    req: KeypadCallCheckRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Guardian checks incoming call number received on an elderly user's keypad phone.
    Returns risk level, category, report count, verification status, and multilingual explanation.
    """
    if len(req.phone_number.strip()) < 7:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Phone number must contain at least 7 characters."
        )

    result = KeypadService.check_keypad_call(
        db=db,
        guardian_user_id=current_user.id,
        phone_number=req.phone_number,
        claimed_caller_identity=req.claimed_caller_identity,
        elderly_user_id=req.elderly_user_id,
        preferred_language=req.preferred_language or "en"
    )
    return KeypadCallCheckResponse(**result)


# ── 4. Scam Number Reporting ─────────────────────────────────────────────────

@router.post("/report-scam", response_model=KeypadScamNumberReportResponse, status_code=status.HTTP_201_CREATED)
def report_keypad_scam_number(
    req: KeypadScamNumberReportRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Submits a predatory phone number targeting an elderly keypad user into the intelligence database.
    Anti-Sybil guard prevents repeated reports from the same guardian inflating count.
    """
    report = KeypadService.report_scam_number(
        db=db,
        guardian_user_id=current_user.id,
        phone_number=req.phone_number,
        fraud_category=req.fraud_category,
        claimed_caller_identity=req.claimed_caller_identity,
        evidence_notes=req.evidence_notes,
        elderly_user_id=req.elderly_user_id
    )

    return KeypadScamNumberReportResponse(
        id=report.id,
        normalized_number=report.normalized_number,
        status="REPORTED",
        message="Predatory phone number recorded in the Keypad Threat Intelligence Repository.",
        verification_status=report.verification_status
    )


# ── 5. Guardian Alert System ─────────────────────────────────────────────────

@router.get("/alerts", response_model=KeypadAlertSummaryResponse)
def get_guardian_alerts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Returns incident history and alert summary for the authenticated guardian.
    Avoids phantom alerts without actual submitted events. Cross-guardian isolated.
    """
    summary = KeypadService.get_guardian_alert_summary(db=db, guardian_user_id=current_user.id)
    return KeypadAlertSummaryResponse(**summary)


@router.post("/alerts/{incident_id}/acknowledge")
def acknowledge_guardian_alert(
    incident_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Marks a threat incident as reviewed / acknowledged by the authenticated guardian."""
    success = KeypadService.acknowledge_incident(db=db, guardian_user_id=current_user.id, incident_id=incident_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incident record not found or does not belong to guardian."
        )
    return {"status": "success", "message": "Incident acknowledged successfully."}


# ── 6. Elderly Fraud Education ───────────────────────────────────────────────

@router.get("/education", response_model=KeypadEducationResponse)
def get_elderly_education(
    lang: str = Query("en", description="Language code: en (English), hi (Hindi), kn (Kannada)")
):
    """
    Returns high-contrast, simple fraud education cards in English, Hindi, or Kannada.
    Includes the Golden Rule and 5 common scam walkthroughs. Public educational endpoint.
    """
    return KeypadEducationResponse(**KeypadService.get_education_content(language=lang))


# ── 7. Official Reporting Guidance ───────────────────────────────────────────

@router.get("/helpdesks", response_model=KeypadOfficialHelpdeskResponse)
def get_official_helpdesks():
    """
    Returns official government reporting portals (Sanchar Saathi Chakshu, 1909, 1930).
    Accurately distinguishes reporting from automatic prevention. Public helpline directory.
    """
    return KeypadOfficialHelpdeskResponse(**KeypadService.get_official_helpdesks())
