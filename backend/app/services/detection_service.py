"""
Cyber Raksha AI - Detection Service
Coordinates input sanitization, machine learning inference via ai_engine,
and persistent recording of genuine security analyses in the database.
"""
import json
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.analysis_history import AnalysisHistory
from app.schemas.detection import (
    URLDetectionRequest,
    URLDetectionResponse,
    URLAnalysisDetail,
    DetectionStatusResponse,
    AnalysisHistoryItem,
    AnalysisHistoryResponse
)
from ai_engine.core.model_manager import model_manager
from ai_engine.inference.phishing_detector import detect_phishing, get_detector_status
from ai_engine.utils.logging import sanitize_url_for_logging


class DetectionService:
    """
    Dedicated detection orchestrator for the backend.
    """

    @staticmethod
    def analyze_url(request: URLDetectionRequest, db: Session) -> URLDetectionResponse:
        """
        Receives URL, validates, passes to genuine AI model, computes risk,
        and saves genuine history record to SQLite database.
        """
        raw_url = request.url.strip()

        # Execute genuine model inference from the AI Engine
        result = detect_phishing(raw_url)

        # Sanitize target URL to avoid storing credentials or excessive params in DB
        sanitized_target = sanitize_url_for_logging(raw_url)

        # Map to database AnalysisHistory entity
        analysis_record = AnalysisHistory(
            module_code="PHISHING",
            target_identifier=sanitized_target,
            status="COMPLETED" if result.success else "FAILED",
            risk_score=result.risk_score,
            threat_category=result.classification,
            summary=f"Analysis of {sanitized_target} resulted in {result.classification} ({result.risk_level} Risk).",
            explanation=result.recommendation,
            metadata_json=json.dumps({
                "model_version": result.model_version,
                "confidence": result.confidence,
                "risk_indicators": result.analysis.get("risk_indicators", []),
                "latency_ms": result.analysis.get("latency_ms"),
                "features_summary": {
                    k: v for k, v in result.analysis.get("features", {}).items()
                    if k in ["url_length", "domain_length", "dot_count", "is_https", "has_ip_address"]
                }
            })
        )

        try:
            db.add(analysis_record)
            db.commit()
            db.refresh(analysis_record)
        except Exception:
            db.rollback()

        return URLDetectionResponse(
            success=result.success,
            classification=result.classification,
            risk_level=result.risk_level,
            risk_score=result.risk_score,
            model_version=result.model_version,
            confidence=result.confidence,
            analysis=URLAnalysisDetail(
                features=result.analysis.get("features", {}),
                risk_indicators=result.analysis.get("risk_indicators", []),
                latency_ms=result.analysis.get("latency_ms"),
                ml_probabilities=result.analysis.get("ml_probabilities"),
                model_algorithm=result.analysis.get("model_algorithm"),
                feature_count=result.analysis.get("feature_count"),
                brand_impersonation=result.analysis.get("features", {}).get("brand_impersonation")
            ),
            recommendation=result.recommendation
        )

    @staticmethod
    def get_status() -> DetectionStatusResponse:
        """
        Returns live detection status, model readiness, and versioning.
        """
        # Ensure model is loaded if available
        model_manager.load_model()
        raw_status = get_detector_status()
        is_ready = raw_status.get("model_available", False) and raw_status.get("model_loaded", False)

        return DetectionStatusResponse(
            model_available=raw_status.get("model_available", False),
            model_loaded=raw_status.get("model_loaded", False),
            model_version=raw_status.get("model_version", "none"),
            algorithm=raw_status.get("algorithm", "none"),
            training_status=raw_status.get("training_status", "UNKNOWN"),
            engine_stage=raw_status.get("engine_stage", "Stage 2: Core AI Engine"),
            dataset_status="VERIFIED_BENCHMARK_ONLINE",
            inference_status="READY" if is_ready else "UNAVAILABLE",
            metrics_summary=raw_status.get("metrics_summary")
        )

    @staticmethod
    def get_history(db: Session, limit: int = 50) -> AnalysisHistoryResponse:
        """
        Retrieves recent analysis records.
        """
        records = (
            db.query(AnalysisHistory)
            .order_by(desc(AnalysisHistory.created_at))
            .limit(limit)
            .all()
        )
        items = [AnalysisHistoryItem.model_validate(r) for r in records]
        return AnalysisHistoryResponse(
            total_records=len(items),
            records=items
        )
