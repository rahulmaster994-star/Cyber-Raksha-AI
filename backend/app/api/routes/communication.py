"""
Cyber Raksha AI - Communication Fraud Detection Routes
Provides endpoints for message threat evaluation, digital-arrest scam detection,
engine health telemetry, and privacy-safe analysis history.
"""
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.communication import (
    CommunicationAnalyzeRequest,
    CommunicationAnalyzeResponse,
    CommunicationStatusResponse
)
from app.schemas.detection import AnalysisHistoryResponse
from app.services.communication_service import CommunicationService

router = APIRouter(prefix="/communication", tags=["Communication Fraud & Digital Arrest"])


@router.post(
    "/analyze",
    response_model=CommunicationAnalyzeResponse,
    status_code=status.HTTP_200_OK,
    summary="Analyze Suspicious Message for Fraud & Social Engineering",
    description="Processes SMS, WhatsApp, Email, or Chat text to detect impersonation, OTP theft, coercion, and phishing."
)
def analyze_communication_message(
    payload: CommunicationAnalyzeRequest,
    db: Session = Depends(get_db)
) -> CommunicationAnalyzeResponse:
    if not payload.message or not payload.message.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The 'message' field cannot be empty or blank."
        )

    if len(payload.message) > 10000:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Message exceeds maximum allowed length of 10,000 characters."
        )

    return CommunicationService.analyze_message(payload, db, is_digital_arrest_focus=False)


@router.post(
    "/digital-arrest/analyze",
    response_model=CommunicationAnalyzeResponse,
    status_code=status.HTTP_200_OK,
    summary="Analyze Message Specifically for Digital Arrest Scam Signatures",
    description="Evaluates presence of fake police/CBI warrants, Aadhaar coercion, video interrogation demands, and safe-account transfers."
)
def analyze_digital_arrest_message(
    payload: CommunicationAnalyzeRequest,
    db: Session = Depends(get_db)
) -> CommunicationAnalyzeResponse:
    if not payload.message or not payload.message.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The 'message' field cannot be empty or blank."
        )

    if len(payload.message) > 10000:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Message exceeds maximum allowed length of 10,000 characters."
        )

    return CommunicationService.analyze_message(payload, db, is_digital_arrest_focus=True)


@router.get(
    "/status",
    response_model=CommunicationStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Communication Detection Engine Telemetry",
    description="Returns live model readiness, active NLP algorithm, and test performance metrics."
)
def get_communication_status() -> CommunicationStatusResponse:
    return CommunicationService.get_status()


@router.get(
    "/history",
    response_model=AnalysisHistoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Communication Fraud Analysis History",
    description="Returns privacy-safe sanitized records of previous message analyses."
)
def get_communication_history(
    limit: int = 50,
    db: Session = Depends(get_db)
) -> AnalysisHistoryResponse:
    return CommunicationService.get_history(db, limit=limit)

