"""
backend/app/api/routes/privacy.py
FastAPI routes for Stage 8: Data Privacy, User Retention Control, and Audit Purging.
"""
from typing import Dict, Any, Optional
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.database.session import get_db
from app.models.incident import UserProtectionSetting
from app.models.analysis_history import AnalysisHistory
from app.models.security_event import SecurityEvent

router = APIRouter(prefix="/privacy", tags=["Stage 8: Privacy & Data Governance"])


class PrivacySettingsUpdate(BaseModel):
    data_retention_days: Optional[int] = Field(None, ge=1, le=365)
    strict_privacy_mode: Optional[bool] = None
    email_alerts_enabled: Optional[bool] = None
    sms_alerts_enabled: Optional[bool] = None
    auto_incident_creation: Optional[bool] = None


class PrivacyPolicyResponse(BaseModel):
    data_collected: Dict[str, str]
    data_stored: Dict[str, str]
    redaction_policies: Dict[str, str]
    external_transfers: Dict[str, str]
    user_rights: Dict[str, str]
    local_storage_engine: str
    retention_period_days: int


@router.get(
    "/policy",
    response_model=PrivacyPolicyResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Platform Privacy and Data Governance Policy",
    description="Returns transparent details on data collection, local SQLite storage, redaction, and user deletion rights."
)
def get_privacy_policy(db: Session = Depends(get_db)):
    setting = db.query(UserProtectionSetting).filter(UserProtectionSetting.user_id == "default_analyst").first()
    retention_days = setting.data_retention_days if setting else 90

    return PrivacyPolicyResponse(
        data_collected={
            "urls": "Submitted URL strings are parsed lexically and structurally for threat indicators.",
            "messages": "Text snippets are checked in-memory for financial coercion and impersonation patterns.",
            "audio": "WAV audio files are processed in-memory for acoustic artifacts. Raw audio is NOT permanently stored on disk."
        },
        data_stored={
            "analysis_history": "Sanitized target identifier, calculated risk score, threat category, and timestamp.",
            "incidents": "Incident number, severity, title, and assigned mitigation action items.",
            "indicators": "Publicly verified threat intelligence feeds (URLhaus, open-source IoCs)."
        },
        redaction_policies={
            "otps": "4-8 digit OTP tokens are automatically masked as [REDACTED_OTP] prior to database logging.",
            "aadhaar": "12-digit Aadhaar / National ID numbers are masked as [REDACTED_AADHAAR].",
            "cards": "16-digit payment card numbers are masked as [REDACTED_CARD].",
            "urls": "Query parameters and basic auth credentials are stripped prior to history logging."
        },
        external_transfers={
            "third_parties": "NO user data is sold, monetized, or shared with third-party tracking services.",
            "threat_feeds": "Threat feed updates pull public blacklists inbound only. User submissions are NOT sent to external APIs by default."
        },
        user_rights={
            "right_to_delete": "Users can purge their entire analysis history or individual records at any time.",
            "retention_control": "Configurable retention period from 1 to 365 days with automated expiry purging."
        },
        local_storage_engine="Local Relational SQLite Database (Encrypted in transit when deployed behind TLS)",
        retention_period_days=retention_days
    )


@router.get(
    "/settings",
    status_code=status.HTTP_200_OK,
    summary="Get User Protection and Privacy Preferences"
)
def get_privacy_settings(db: Session = Depends(get_db)):
    setting = db.query(UserProtectionSetting).filter(UserProtectionSetting.user_id == "default_analyst").first()
    if not setting:
        setting = UserProtectionSetting(user_id="default_analyst")
        db.add(setting)
        db.commit()
        db.refresh(setting)

    return {
        "user_id": setting.user_id,
        "data_retention_days": setting.data_retention_days,
        "strict_privacy_mode": setting.strict_privacy_mode,
        "auto_incident_creation": setting.auto_incident_creation,
        "email_alerts_enabled": setting.email_alerts_enabled,
        "sms_alerts_enabled": setting.sms_alerts_enabled,
        "updated_at": setting.updated_at.isoformat() if setting.updated_at else None
    }


@router.patch(
    "/settings",
    status_code=status.HTTP_200_OK,
    summary="Update Privacy Preferences and Retention Limits"
)
def update_privacy_settings(
    payload: PrivacySettingsUpdate,
    db: Session = Depends(get_db)
):
    setting = db.query(UserProtectionSetting).filter(UserProtectionSetting.user_id == "default_analyst").first()
    if not setting:
        setting = UserProtectionSetting(user_id="default_analyst")
        db.add(setting)

    if payload.data_retention_days is not None:
        setting.data_retention_days = payload.data_retention_days
    if payload.strict_privacy_mode is not None:
        setting.strict_privacy_mode = payload.strict_privacy_mode
    if payload.auto_incident_creation is not None:
        setting.auto_incident_creation = payload.auto_incident_creation
    if payload.email_alerts_enabled is not None:
        setting.email_alerts_enabled = payload.email_alerts_enabled
    if payload.sms_alerts_enabled is not None:
        setting.sms_alerts_enabled = payload.sms_alerts_enabled

    db.commit()
    db.refresh(setting)

    return {
        "status": "SUCCESS",
        "message": "Privacy settings updated successfully.",
        "settings": {
            "data_retention_days": setting.data_retention_days,
            "strict_privacy_mode": setting.strict_privacy_mode,
            "auto_incident_creation": setting.auto_incident_creation
        }
    }


@router.delete(
    "/history",
    status_code=status.HTTP_200_OK,
    summary="Purge Stored Analysis History",
    description="Permanently deletes user analysis history records. Optional module filter (e.g. PHISHING, COMM_RISK, VOICE_DETECT)."
)
def purge_analysis_history(
    module_code: Optional[str] = Query(None, description="Optional filter by module code"),
    db: Session = Depends(get_db)
):
    query = db.query(AnalysisHistory)
    if module_code:
        query = query.filter(AnalysisHistory.module_code == module_code.upper())

    count = query.count()
    query.delete(synchronize_session=False)

    # Log security event for audit trail
    sec_event = SecurityEvent(
        event_type="PRIVACY_HISTORY_PURGED",
        severity="INFO",
        source_component="PRIVACY_CONTROLLER",
        description=f"User purged {count} analysis history records (filter: {module_code or 'ALL'})."
    )
    db.add(sec_event)
    db.commit()

    return {
        "status": "SUCCESS",
        "deleted_records_count": count,
        "message": f"Successfully purged {count} analysis history record(s)."
    }


@router.delete(
    "/history/{history_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete Specific Historical Analysis Record"
)
def delete_single_history_record(
    history_id: int,
    db: Session = Depends(get_db)
):
    rec = db.query(AnalysisHistory).filter(AnalysisHistory.id == history_id).first()
    if not rec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Analysis history record with ID {history_id} not found."
        )

    db.delete(rec)
    db.commit()

    return {
        "status": "SUCCESS",
        "deleted_id": history_id,
        "message": f"Analysis record {history_id} deleted permanently."
    }


@router.post(
    "/cleanup-expired",
    status_code=status.HTTP_200_OK,
    summary="Purge Records Exceeding Data Retention Window",
    description="Automated retention maintenance: removes analysis history records older than configured data_retention_days."
)
def cleanup_expired_records(db: Session = Depends(get_db)):
    setting = db.query(UserProtectionSetting).filter(UserProtectionSetting.user_id == "default_analyst").first()
    days = setting.data_retention_days if setting else 90

    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    expired_records = db.query(AnalysisHistory).filter(AnalysisHistory.created_at < cutoff)
    count = expired_records.count()
    expired_records.delete(synchronize_session=False)
    db.commit()

    return {
        "status": "SUCCESS",
        "retention_days_limit": days,
        "purged_records_count": count,
        "cutoff_timestamp": cutoff.isoformat()
    }

