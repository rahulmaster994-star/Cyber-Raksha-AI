"""
Cyber Raksha AI - Phishing Detector Inference Interface
Provides the public prediction API for backend consumption.
"""
from typing import Dict, Any
from ai_engine.core.engine import ai_engine
from ai_engine.core.model_manager import model_manager
from ai_engine.core.prediction import DetectionResult


def detect_phishing(url: str) -> DetectionResult:
    """
    Evaluates whether a given URL is legitimate, phishing, suspicious, or inconclusive.
    """
    return ai_engine.predict_url(url)


def get_detector_status() -> Dict[str, Any]:
    """
    Returns live detector operational health, model version, and availability.
    """
    model_status = model_manager.get_status()
    metadata = model_manager.get_metadata()
    return {
        "engine_version": ai_engine.version,
        "engine_stage": ai_engine.stage,
        "model_available": model_status["model_available"],
        "model_loaded": model_status["model_loaded"],
        "model_version": model_status["model_version"],
        "algorithm": model_status["algorithm"],
        "training_status": model_status["training_status"],
        "metrics_summary": metadata.get("test_metrics", {})
    }
