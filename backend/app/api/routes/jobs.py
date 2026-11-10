"""
backend/app/api/routes/jobs.py
FastAPI routes for Stage 9 Real-Time Analysis Job Management & SSE Streaming.
"""
from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.core.job_manager import job_manager
from app.core.feature_flags import feature_flags
from ai_engine.inference.phishing_detector import detect_phishing
from ai_engine.inference.communication_detector import communication_detector
from ai_engine.threat_intelligence.intelligence_engine import intelligence_engine

router = APIRouter(prefix="/jobs", tags=["Stage 9: Analysis Job Management & Real-Time Streaming"])


class JobSubmitRequest(BaseModel):
    job_type: str = Field(..., description="URL_ANALYSIS, COMM_ANALYSIS, or UNIFIED_ANALYSIS")
    url: Optional[str] = None
    message: Optional[str] = None
    is_digital_arrest: bool = False


def _execute_job_sync(job_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """Synchronous worker target executed inside job_executor thread pool."""
    if job_type == "URL_ANALYSIS":
        url = payload.get("url", "")
        res = detect_phishing(url)
        return {
            "classification": res.classification,
            "risk_level": res.risk_level,
            "risk_score": res.risk_score,
            "confidence": res.confidence,
            "recommendation": res.recommendation,
            "analysis": res.analysis
        }
    elif job_type == "COMM_ANALYSIS":
        msg = payload.get("message", "")
        return communication_detector.analyze_message(msg)
    elif job_type == "UNIFIED_ANALYSIS":
        return intelligence_engine.analyze_unified(
            url=payload.get("url"),
            message=payload.get("message"),
            is_digital_arrest=payload.get("is_digital_arrest", False)
        )
    else:
        raise ValueError(f"Unsupported job type: {job_type}")


@router.post(
    "/submit",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Submit Asynchronous Analysis Job",
    description="Enqueues a long-running threat analysis job and returns an immediate Job ID for tracking."
)
async def submit_analysis_job(
    request: JobSubmitRequest,
    background_tasks: BackgroundTasks
):
    if not feature_flags.is_enabled("enable_async_jobs"):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Asynchronous job queueing is currently disabled by administrator feature flag."
        )

    valid_types = {"URL_ANALYSIS", "COMM_ANALYSIS", "UNIFIED_ANALYSIS"}
    if request.job_type not in valid_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid job_type '{request.job_type}'. Must be one of {valid_types}."
        )

    payload = {
        "url": request.url,
        "message": request.message,
        "is_digital_arrest": request.is_digital_arrest
    }

    job = job_manager.create_job(request.job_type, payload)

    # Dispatch to background task runner
    background_tasks.add_task(
        job_manager.run_job_async,
        job,
        _execute_job_sync,
        request.job_type,
        payload
    )

    return {
        "job_id": job.job_id,
        "job_type": job.job_type,
        "status": job.status,
        "progress_percent": job.progress_percent,
        "progress_message": job.progress_message,
        "created_at": job.created_at,
        "tracking_url": f"/api/v1/jobs/{job.job_id}",
        "stream_url": f"/api/v1/jobs/{job.job_id}/stream"
    }


@router.get(
    "/{job_id}",
    status_code=status.HTTP_200_OK,
    summary="Get Job Status and Result"
)
def get_job_status(job_id: str):
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with ID '{job_id}' not found."
        )
    return job.to_dict()


@router.get(
    "/{job_id}/stream",
    summary="Stream Real-Time Job Progress (Server-Sent Events)"
)
async def stream_job_progress(job_id: str):
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with ID '{job_id}' not found."
        )

    return StreamingResponse(
        job_manager.stream_job_events(job_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    summary="List Recent Analysis Jobs"
)
def list_analysis_jobs(limit: int = Query(20, ge=1, le=100)):
    return {
        "total_active_jobs": len(job_manager._jobs),
        "jobs": job_manager.list_jobs(limit)
    }


@router.post(
    "/{job_id}/cancel",
    status_code=status.HTTP_200_OK,
    summary="Cancel Analysis Job"
)
def cancel_analysis_job(job_id: str):
    cancelled = job_manager.cancel_job(job_id)
    if not cancelled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Job '{job_id}' could not be cancelled (either not found or already completed/failed)."
        )
    return {
        "status": "SUCCESS",
        "job_id": job_id,
        "message": "Job marked as CANCELLED."
    }

