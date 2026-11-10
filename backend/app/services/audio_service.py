"""
backend/app/services/audio_service.py
Service layer orchestrating Stage 4 Audio Analysis, database recording,
and telemetry retrieval.
"""
import json
from typing import Optional
from fastapi import UploadFile, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.analysis_history import AnalysisHistory
from app.schemas.detection import AnalysisHistoryItem, AnalysisHistoryResponse
from app.schemas.audio import (
    AudioAnalysisResponse,
    AudioStatusResponse,
    AudioMetadataSchema,
    AudioIndicatorSchema
)
from ai_engine.inference.audio_detector import audio_detector
from ai_engine.audio.audio_validator import AudioValidationError
from ai_engine.audio.audio_preprocessor import AudioPreprocessingError


class AudioService:
    @staticmethod
    async def analyze_audio_upload(
        file: UploadFile,
        db: Session
    ) -> AudioAnalysisResponse:
        """
        Processes an uploaded audio file, executes Stage 4 detection pipeline,
        and logs analysis securely to the database.
        """
        # Read file bytes in memory (streamed)
        try:
            file_bytes = await file.read()
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to read uploaded audio file: {e}"
            )

        filename = file.filename or "uploaded_voice.wav"

        try:
            # Execute inference
            result = audio_detector.analyze_audio(
                file_bytes=file_bytes,
                filename=filename,
                content_type=file.content_type
            )
        except AudioValidationError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except AudioPreprocessingError as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=str(e)
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Audio analysis error: {e}"
            )

        # Store in database
        # Sanitized identifier: only filename and duration, never raw audio data!
        meta = result.get("audio_metadata", {})
        target_id = f"{filename} ({meta.get('duration_seconds', 0)}s, {meta.get('format', 'WAV')})"

        analysis_record = AnalysisHistory(
            module_code="VOICE_DETECT",
            target_identifier=target_id,
            status="COMPLETED",
            risk_score=result["risk_score"],
            threat_category=result["classification"],
            summary=f"Voice Deepfake Analysis: {result['classification']} ({result['risk_level']} Risk, {result['risk_score']}/100)",
            explanation=result["explanation"],
            metadata_json=json.dumps({
                "confidence": result["confidence"],
                "ml_probability": result["ml_probability"],
                "indicators_count": result["indicators_count"],
                "indicators": [ind["code"] for ind in result.get("detected_indicators", [])],
                "audio_metadata": meta,
                "engine_version": result["engine_version"]
            })
        )

        try:
            db.add(analysis_record)
            db.commit()
            db.refresh(analysis_record)
        except Exception as e:
            db.rollback()
            print(f"[AudioService] DB commit error: {e}")

        # Map to Pydantic schema
        indicators = [
            AudioIndicatorSchema(**ind) for ind in result.get("detected_indicators", [])
        ]
        meta_schema = AudioMetadataSchema(**meta)

        return AudioAnalysisResponse(
            status="SUCCESS",
            classification=result["classification"],
            risk_level=result["risk_level"],
            risk_score=result["risk_score"],
            confidence=result["confidence"],
            ml_probability=result["ml_probability"],
            indicator_score=result["indicator_score"],
            indicators_count=result["indicators_count"],
            detected_indicators=indicators,
            spectral_metrics=result.get("spectral_metrics", {}),
            audio_metadata=meta_schema,
            explanation=result["explanation"],
            recommendations=result["recommendations"],
            is_inconclusive=result.get("is_inconclusive", False),
            inconclusive_reason=result.get("inconclusive_reason"),
            engine_version=result["engine_version"],
            model_version=result.get("model_version")
        )

    @staticmethod
    def get_status() -> AudioStatusResponse:
        """Fetch engine health, model loaded status, and algorithm metadata."""
        raw_status = audio_detector.get_status()
        return AudioStatusResponse(
            module=raw_status["module"],
            model_available=raw_status["model_available"],
            model_loaded=raw_status["model_loaded"],
            model_name=raw_status["model_name"],
            model_type=raw_status["model_type"],
            stage=raw_status["stage"],
            accuracy=raw_status.get("accuracy"),
            features_count=raw_status["features_count"],
            supported_formats=raw_status["supported_formats"],
            disclaimer=raw_status["disclaimer"]
        )

    @staticmethod
    def get_history(db: Session, limit: int = 20) -> AnalysisHistoryResponse:
        """Retrieve recent audio analysis logs."""
        records = (
            db.query(AnalysisHistory)
            .filter(AnalysisHistory.module_code == "VOICE_DETECT")
            .order_by(desc(AnalysisHistory.created_at))
            .limit(limit)
            .all()
        )
        items = [AnalysisHistoryItem.model_validate(r) for r in records]
        return AnalysisHistoryResponse(
            total_records=len(items),
            records=items
        )

    @staticmethod
    def get_analysis_by_id(db: Session, analysis_id: int) -> Optional[AnalysisHistoryItem]:
        """Fetch a specific audio analysis record."""
        record = (
            db.query(AnalysisHistory)
            .filter(
                AnalysisHistory.id == analysis_id,
                AnalysisHistory.module_code == "VOICE_DETECT"
            )
            .first()
        )
        if not record:
            return None
        return AnalysisHistoryItem.model_validate(record)

