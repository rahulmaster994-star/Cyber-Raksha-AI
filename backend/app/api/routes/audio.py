"""
backend/app/api/routes/audio.py
FastAPI routes for Stage 4: Voice Deepfake & Audio Impersonation Detection.
"""
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.services.audio_service import AudioService
from app.schemas.audio import AudioAnalysisResponse, AudioStatusResponse
from app.schemas.detection import AnalysisHistoryResponse, AnalysisHistoryItem

router = APIRouter(prefix="/audio", tags=["Stage 4: Audio Deepfake Detection"])


@router.post(
    "/analyze",
    response_model=AudioAnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Analyze Audio for AI Voice Cloning & Impersonation",
    description="Upload a WAV audio recording (e.g. suspicious phone call or voice note) to detect synthetic speech, deepfake artifacts, and cloning indicators."
)
async def analyze_audio(
    file: UploadFile = File(..., description="WAV format audio recording to analyze"),
    db: Session = Depends(get_db)
):
    return await AudioService.analyze_audio_upload(file, db)


@router.get(
    "/status",
    response_model=AudioStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Audio Detection Model Status",
    description="Returns telemetry and status of the Voice Cloning & Deepfake detection model."
)
def get_audio_status():
    return AudioService.get_status()


@router.get(
    "/history",
    response_model=AnalysisHistoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Audio Analysis History",
    description="Returns recent voice analysis records from the database."
)
def get_audio_history(
    limit: int = 20,
    db: Session = Depends(get_db)
):
    return AudioService.get_history(db, limit)


@router.get(
    "/analysis/{analysis_id}",
    response_model=AnalysisHistoryItem,
    status_code=status.HTTP_200_OK,
    summary="Get Specific Audio Analysis Record",
    description="Retrieve a historical audio analysis record by ID."
)
def get_analysis_by_id(
    analysis_id: int,
    db: Session = Depends(get_db)
):
    record = AudioService.get_analysis_by_id(db, analysis_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Audio analysis record with ID {analysis_id} not found."
        )
    return record

