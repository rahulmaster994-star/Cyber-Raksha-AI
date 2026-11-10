"""
Cyber Raksha AI - Communication Fraud Detection Service
Coordinates input sanitization, privacy redaction, ML inference via ai_engine,
and persistent recording of genuine communication threat analyses in SQLite.
"""
import json
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.analysis_history import AnalysisHistory
from app.schemas.communication import (
    CommunicationAnalyzeRequest,
    CommunicationAnalyzeResponse,
    CommunicationAnalysisDetail,
    IndicatorsBreakdown,
    CommunicationStatusResponse
)
from app.schemas.detection import (
    AnalysisHistoryItem,
    AnalysisHistoryResponse
)
from ai_engine.inference.communication_detector import communication_detector
from ai_engine.communication.text_preprocessor import sanitize_message_for_storage


class CommunicationService:
    """
    Service layer orchestrating NLP communication fraud detection.
    """

    @staticmethod
    def analyze_message(
        request: CommunicationAnalyzeRequest,
        db: Session,
        is_digital_arrest_focus: bool = False
    ) -> CommunicationAnalyzeResponse:
        raw_msg = request.message.strip()

        # Run genuine AI inference
        result = communication_detector.analyze_message(raw_msg)

        # Sanitize message before persistence to protect personal credentials & PII
        sanitized_snippet = sanitize_message_for_storage(raw_msg, max_length=120)

        module_code = "COMM_RISK" if not is_digital_arrest_focus else "DIGITAL_ARREST"

        # Log genuine analysis history to database
        analysis_record = AnalysisHistory(
            module_code=module_code,
            target_identifier=sanitized_snippet,
            status="COMPLETED" if result.get("success", False) else "FAILED",
            risk_score=result.get("risk_score", 0.0),
            threat_category=result.get("classification", "UNKNOWN"),
            summary=result.get("explanation", ""),
            explanation="; ".join(result.get("recommendations", [])),
            metadata_json=json.dumps({
                "model_version": result.get("model_version"),
                "confidence": result.get("confidence"),
                "detected_indicators": result.get("detected_indicators", []),
                "analysis": result.get("analysis", {})
            })
        )

        try:
            db.add(analysis_record)
            db.commit()
            db.refresh(analysis_record)
        except Exception:
            db.rollback()

        analysis_meta = result.get("analysis", {})
        indicators_b = analysis_meta.get("indicators_breakdown", {})

        return CommunicationAnalyzeResponse(
            success=result.get("success", False),
            classification=result.get("classification", "UNKNOWN"),
            risk_level=result.get("risk_level", "LOW"),
            risk_score=result.get("risk_score", 0.0),
            confidence=result.get("confidence"),
            detected_indicators=result.get("detected_indicators", []),
            explanation=result.get("explanation", ""),
            recommendations=result.get("recommendations", []),
            model_version=result.get("model_version", "v1.0.0"),
            analysis=CommunicationAnalysisDetail(
                latency_ms=analysis_meta.get("latency_ms"),
                model_algorithm=analysis_meta.get("model_algorithm"),
                ml_fraud_probability=analysis_meta.get("ml_fraud_probability"),
                indicators_breakdown=IndicatorsBreakdown(**indicators_b) if indicators_b else None,
                is_digital_arrest_candidate=analysis_meta.get("is_digital_arrest_candidate", False)
            )
        )

    @staticmethod
    def get_status() -> CommunicationStatusResponse:
        raw_status = communication_detector.get_status()
        return CommunicationStatusResponse(
            model_available=raw_status.get("model_available", False),
            model_loaded=raw_status.get("model_loaded", False),
            model_version=raw_status.get("model_version", "none"),
            algorithm=raw_status.get("algorithm", "none"),
            engine_stage=raw_status.get("engine_stage", "Stage 3"),
            training_status=raw_status.get("training_status", "UNKNOWN"),
            inference_status=raw_status.get("inference_status", "UNAVAILABLE"),
            metrics_summary=raw_status.get("metrics_summary")
        )

    @staticmethod
    def get_history(db: Session, limit: int = 50) -> AnalysisHistoryResponse:
        records = (
            db.query(AnalysisHistory)
            .filter(AnalysisHistory.module_code.in_(["COMM_RISK", "DIGITAL_ARREST"]))
            .order_by(desc(AnalysisHistory.created_at))
            .limit(limit)
            .all()
        )
        items = [AnalysisHistoryItem.model_validate(r) for r in records]
        return AnalysisHistoryResponse(
            total_records=len(items),
            records=items
        )

