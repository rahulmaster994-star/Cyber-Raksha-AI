"""
backend/app/api/routes/admin.py
Stage 9: Administrator Operations Center.
Protected by X-Admin-Key header matching settings.ADMIN_SECRET_KEY.
Provides system overview, feature flags, feedback review queue, alert management,
and model improvement pipeline controls.
"""
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Header, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.feature_flags import feature_flags
from app.core.alert_manager import alert_manager
from app.core.observability import metrics_tracker, get_detailed_health_status
from app.core.job_manager import job_manager
from app.services.model_monitor import model_monitor
from app.services.threat_intel_ops import threat_intel_ops
from app.models.feedback import AnalysisFeedback
from app.database.session import get_db

router = APIRouter(tags=["Admin Operations Center"])

# ---------------------------------------------------------------------------
# Admin authentication dependency
# ---------------------------------------------------------------------------

def require_admin_key(x_admin_key: Optional[str] = Header(None, alias="x-admin-key")):
    """
    Validates the X-Admin-Key request header against ADMIN_SECRET_KEY in config.
    Returns 401 if key is missing or incorrect.
    """
    if not x_admin_key or x_admin_key != settings.ADMIN_SECRET_KEY:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={
                "error": "Unauthorized",
                "message": (
                    "A valid X-Admin-Key header is required to access admin endpoints. "
                    "Set ADMIN_SECRET_KEY in your backend .env file."
                ),
            },
        )
    return True


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------

class FeatureFlagUpdate(BaseModel):
    enabled: bool


class ReviewUpdateRequest(BaseModel):
    review_status: str = Field(
        ...,
        description="UNDER_REVIEW | CONFIRMED | REJECTED | INCONCLUSIVE",
    )
    reviewer_notes: Optional[str] = Field(None, max_length=2000)
    reviewed_by: Optional[str] = Field(None, max_length=100)

    model_config = {"str_strip_whitespace": True}


VALID_REVIEW_STATUSES = {
    "UNDER_REVIEW",
    "CONFIRMED",
    "REJECTED",
    "INCONCLUSIVE",
}

# ---------------------------------------------------------------------------
# Admin Routes
# ---------------------------------------------------------------------------


@router.get(
    "/admin/overview",
    status_code=status.HTTP_200_OK,
    summary="Admin System Overview",
    description="Complete system health, model status, feed status, job queue summary, and active alerts.",
)
def admin_overview(auth=Depends(require_admin_key)):
    if isinstance(auth, JSONResponse):
        return auth

    health = get_detailed_health_status()
    metrics = metrics_tracker.get_metrics_summary()
    feed_report = threat_intel_ops.get_feed_health_report()
    models_overview = model_monitor.get_models_overview()
    jobs_summary = job_manager.list_jobs(limit=5)
    alerts_summary = alert_manager.get_summary()
    flags = feature_flags.get_all_flags()

    return {
        "platform": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "stage": settings.STAGE,
        "overall_health": health["status"],
        "subsystems": health["services"],
        "performance": {
            "total_requests": metrics["total_requests"],
            "error_rate_percent": metrics["error_rate_percent"],
            "p95_latency_ms": metrics["latency_ms"]["p95"],
            "uptime_seconds": metrics["uptime_seconds"],
        },
        "threat_intel": {
            "healthy_sources": feed_report["summary"]["healthy_sources"],
            "total_active_indicators": feed_report["summary"]["total_active_indicators_in_db"],
        },
        "ai_models": {
            "total_deployed": models_overview["total_deployed_models"],
        },
        "jobs": {
            "recent": [
                {
                    "job_id": j["job_id"],
                    "status": j["status"],
                    "job_type": j["job_type"],
                }
                for j in jobs_summary
            ]
        },
        "alerts": alerts_summary,
        "feature_flags": {k: v["enabled"] for k, v in flags.items()},
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get(
    "/admin/feature-flags",
    status_code=status.HTTP_200_OK,
    summary="List All Feature Flags",
)
def list_feature_flags(auth=Depends(require_admin_key)):
    if isinstance(auth, JSONResponse):
        return auth
    return {
        "feature_flags": feature_flags.get_all_flags(),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.patch(
    "/admin/feature-flags/{flag_name}",
    status_code=status.HTTP_200_OK,
    summary="Enable or Disable a Feature Flag",
)
def update_feature_flag(
    flag_name: str,
    payload: FeatureFlagUpdate,
    auth=Depends(require_admin_key),
):
    if isinstance(auth, JSONResponse):
        return auth

    success = feature_flags.set_flag(flag_name, payload.enabled)
    if not success:
        all_flags = list(feature_flags.get_all_flags().keys())
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "error": "Flag Not Found",
                "detail": f"'{flag_name}' is not a registered feature flag.",
                "valid_flags": all_flags,
            },
        )

    return {
        "flag_name": flag_name,
        "enabled": payload.enabled,
        "message": f"Feature flag '{flag_name}' has been {'enabled' if payload.enabled else 'disabled'}.",
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }


@router.get(
    "/admin/feedback/pending",
    status_code=status.HTTP_200_OK,
    summary="List Pending Feedback for Human Review",
)
def list_pending_feedback(
    limit: int = 20,
    auth=Depends(require_admin_key),
    db: Session = Depends(get_db),
):
    if isinstance(auth, JSONResponse):
        return auth

    limit = max(1, min(limit, 100))
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
        ],
    }


@router.patch(
    "/admin/feedback/{feedback_id}/review",
    status_code=status.HTTP_200_OK,
    summary="Submit Human Review Verdict on Feedback",
)
def review_feedback(
    feedback_id: int,
    payload: ReviewUpdateRequest,
    auth=Depends(require_admin_key),
    db: Session = Depends(get_db),
):
    if isinstance(auth, JSONResponse):
        return auth

    new_status = payload.review_status.upper()
    if new_status not in VALID_REVIEW_STATUSES:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": "Invalid Review Status",
                "detail": f"'{payload.review_status}' is not valid.",
                "valid_statuses": sorted(VALID_REVIEW_STATUSES),
            },
        )

    record = db.query(AnalysisFeedback).filter(AnalysisFeedback.id == feedback_id).first()
    if not record:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"error": "Not Found", "detail": f"Feedback ID {feedback_id} not found."},
        )

    record.review_status = new_status
    record.reviewer_notes = payload.reviewer_notes
    record.reviewed_by = payload.reviewed_by
    record.reviewed_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(record)

    return {
        "feedback_id": record.id,
        "new_review_status": record.review_status,
        "reviewed_by": record.reviewed_by,
        "reviewed_at": record.reviewed_at.isoformat() if record.reviewed_at else None,
        "message": "Review verdict recorded. No automatic model changes will be made.",
    }


@router.get(
    "/admin/alerts",
    status_code=status.HTTP_200_OK,
    summary="List Recent Operational Alerts",
)
def list_alerts(limit: int = 50, auth=Depends(require_admin_key)):
    if isinstance(auth, JSONResponse):
        return auth

    return {
        "summary": alert_manager.get_summary(),
        "alerts": alert_manager.get_all_alerts(limit=limit),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.post(
    "/admin/alerts/clear",
    status_code=status.HTTP_200_OK,
    summary="Acknowledge All Active Alerts",
)
def clear_alerts(auth=Depends(require_admin_key)):
    if isinstance(auth, JSONResponse):
        return auth

    acknowledged_count = alert_manager.acknowledge_all()
    return {
        "acknowledged_count": acknowledged_count,
        "message": f"{acknowledged_count} alert(s) acknowledged.",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.post(
    "/admin/alerts/{alert_id}/acknowledge",
    status_code=status.HTTP_200_OK,
    summary="Acknowledge a Single Alert",
)
def acknowledge_alert(alert_id: str, auth=Depends(require_admin_key)):
    if isinstance(auth, JSONResponse):
        return auth

    success = alert_manager.acknowledge_alert(alert_id)
    if not success:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"error": "Not Found", "detail": f"Alert '{alert_id}' not found."},
        )
    return {
        "alert_id": alert_id,
        "acknowledged": True,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get(
    "/admin/model-candidates",
    status_code=status.HTTP_200_OK,
    summary="Model Improvement Pipeline Status",
    description=(
        "Returns the current state of the controlled model improvement pipeline. "
        "No automatic retraining occurs without manual administrator approval."
    ),
)
def model_pipeline_status(auth=Depends(require_admin_key)):
    if isinstance(auth, JSONResponse):
        return auth

    models = model_monitor.get_models_overview()
    return {
        "pipeline_status": "MANUAL_REVIEW_REQUIRED",
        "governance_statement": (
            "Model updates require: (1) labeled ground-truth test set, "
            "(2) offline evaluation exceeding current benchmark, "
            "(3) administrator approval, (4) staged rollout. "
            "Automatic retraining from user feedback or input drift is strictly prohibited."
        ),
        "current_models": [
            {
                "model_id": m["model_id"],
                "version": m["model_version"],
                "status": m["deployment_status"],
                "f1_score": m["metrics"].get("f1_score"),
                "evaluation_date": m["evaluation_date"],
            }
            for m in models["models"]
        ],
        "pending_candidates": [],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.post(
    "/admin/model/{model_id}/rollback",
    status_code=status.HTTP_200_OK,
    summary="Record Model Rollback Event",
    description=(
        "Records a model rollback event in the operations log. "
        "Actual model file replacement must be performed manually by an engineer."
    ),
)
def record_model_rollback(model_id: str, auth=Depends(require_admin_key)):
    if isinstance(auth, JSONResponse):
        return auth

    alert_manager.create_alert(
        alert_type="BACKEND_DEGRADED",
        source=f"MODEL_ROLLBACK_{model_id.upper()}",
        message=f"Model rollback event recorded for '{model_id}'. Manual file replacement required.",
        severity="WARNING",
    )

    return {
        "model_id": model_id,
        "event": "ROLLBACK_RECORDED",
        "message": (
            f"Rollback event for '{model_id}' has been logged. "
            "An engineer must manually replace the .joblib model file and restart the backend."
        ),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

