"""
backend/app/api/routes/threat_intel.py
FastAPI route endpoints for Stage 5: Threat Intelligence & Unified Risk Assessment.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.services.threat_intel_service import ThreatIntelService
from app.schemas.threat_intel import (
    ThreatSearchRequest,
    ThreatSearchResponse,
    ThreatIntelStatusResponse,
    ThreatIndicatorSchema,
    UnifiedAnalyzeRequest,
    UnifiedAnalyzeResponse,
    LiveThreatEvent
)

router = APIRouter(prefix="/intel", tags=["Stage 5: Threat Intelligence & Unified Risk"])


@router.get(
    "/status",
    response_model=ThreatIntelStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Threat Intelligence Engine Status",
    description="Returns threat intelligence database statistics, sources, and feed telemetry."
)
def get_intel_status():
    return ThreatIntelService.get_status()


@router.post(
    "/search",
    response_model=ThreatSearchResponse,
    status_code=status.HTTP_200_OK,
    summary="Search Threat Intelligence IoC Explorer",
    description="Search any URL, domain name, or IP address against verified cybersecurity feeds."
)
def search_threat_indicator(request: ThreatSearchRequest):
    return ThreatIntelService.search_indicator(
        query=request.query,
        indicator_type=request.indicator_type
    )


@router.post(
    "/feed/update",
    status_code=status.HTTP_200_OK,
    summary="Trigger Threat Feed Update",
    description="Fetches the latest verified malicious URLs from URLhaus community API."
)
def trigger_feed_update(db: Session = Depends(get_db)):
    return ThreatIntelService.trigger_feed_update(db)


@router.get(
    "/indicators",
    response_model=List[ThreatIndicatorSchema],
    status_code=status.HTTP_200_OK,
    summary="List Verified Threat Indicators",
    description="Returns active indicators of compromise from verified threat intelligence feeds."
)
def list_indicators(limit: int = 50, active_only: bool = True):
    return ThreatIntelService.get_verified_indicators(limit=limit, active_only=active_only)


@router.get(
    "/scheduler/status",
    status_code=status.HTTP_200_OK,
    summary="Get Threat Intel Scheduler Status",
    description="Returns real-time execution telemetry of the background threat intelligence synchronization scheduler."
)
def get_scheduler_status():
    from app.services.threat_intel_scheduler import threat_intel_scheduler
    return threat_intel_scheduler.get_telemetry()


@router.post(
    "/scheduler/trigger",
    status_code=status.HTTP_200_OK,
    summary="Trigger Immediate Threat Intel Scheduler Cycle",
    description="Forces an immediate execution of the background threat feed synchronization and indicator cleanup."
)
async def trigger_scheduler_cycle():
    from app.services.threat_intel_scheduler import threat_intel_scheduler
    return await threat_intel_scheduler.run_sync_cycle()


@router.post(
    "/unified/analyze",
    response_model=UnifiedAnalyzeResponse,
    status_code=status.HTTP_200_OK,
    summary="Unified Multi-Vector Threat Analysis",
    description="Analyzes submitted URLs, messages, and social engineering context using cross-module correlation."
)
def analyze_unified_text(
    request: UnifiedAnalyzeRequest,
    db: Session = Depends(get_db)
):
    return ThreatIntelService.analyze_unified(
        db=db,
        url=request.url,
        message=request.message,
        is_digital_arrest=request.is_digital_arrest
    )


@router.post(
    "/unified/analyze-audio",
    response_model=UnifiedAnalyzeResponse,
    status_code=status.HTTP_200_OK,
    summary="Unified Multi-Modal Analysis with Audio Upload",
    description="Multipart upload supporting simultaneous inspection of voice recording with accompanying message text."
)
async def analyze_unified_with_audio(
    file: UploadFile = File(..., description="WAV voice recording"),
    message: Optional[str] = Form(None, description="Accompanying extortion/phishing message text"),
    url: Optional[str] = Form(None, description="Accompanying suspicious URL"),
    db: Session = Depends(get_db)
):
    file_bytes = await file.read()
    return ThreatIntelService.analyze_unified(
        db=db,
        url=url,
        message=message,
        is_digital_arrest=False,
        audio_bytes=file_bytes,
        audio_filename=file.filename
    )


@router.get(
    "/events/live",
    response_model=List[LiveThreatEvent],
    status_code=status.HTTP_200_OK,
    summary="Live Security Events Stream",
    description="Returns recent real-time security events logged across the unified detection platform."
)
def get_live_events(
    limit: int = 20,
    db: Session = Depends(get_db)
):
    return ThreatIntelService.get_live_events(db, limit)

