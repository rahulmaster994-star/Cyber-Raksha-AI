"""
Cyber Raksha AI - Detection API Routes
Exposes URL threat analysis, model readiness telemetry, and analysis history.
"""
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.core.security import validate_safe_url
from app.schemas.detection import (
    URLDetectionRequest,
    URLDetectionResponse,
    DetectionStatusResponse,
    AnalysisHistoryResponse
)
from app.services.detection_service import DetectionService

router = APIRouter(prefix="/detection", tags=["AI Threat Detection"])


@router.post(
    "/url",
    response_model=URLDetectionResponse,
    status_code=status.HTTP_200_OK,
    summary="Analyze URL for Phishing & Threat Indicators",
    description="Processes target URL with real ML model inference, extracts structural features, and returns risk profile."
)
def detect_url_phishing(
    payload: URLDetectionRequest,
    db: Session = Depends(get_db)
) -> URLDetectionResponse:
    # Security input validation: scheme, length, dangerous protocol checks
    safe_url = validate_safe_url(payload.url)
    payload.url = safe_url

    return DetectionService.analyze_url(payload, db)


@router.get(
    "/status",
    response_model=DetectionStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Detection Engine Readiness & Model Telemetry",
    description="Reports model availability, version, loaded algorithm, and metrics summary."
)
def get_detection_status() -> DetectionStatusResponse:
    return DetectionService.get_status()


@router.get(
    "/history",
    response_model=AnalysisHistoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Analysis History Records",
    description="Returns genuine stored records of previous analyses from the database."
)
def get_detection_history(
    limit: int = 50,
    db: Session = Depends(get_db)
) -> AnalysisHistoryResponse:
    return DetectionService.get_history(db, limit=limit)

