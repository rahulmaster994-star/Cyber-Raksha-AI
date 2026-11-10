"""
Cyber Raksha AI - Communication Detector Inference Engine
Coordinates message normalization, TF-IDF NLP inference, multi-vector
heuristic feature extraction, explainable risk assessment, and Digital Arrest detection.
"""
import json
import time
from pathlib import Path
from typing import Dict, Any, Optional
import joblib
import numpy as np

from ai_engine.communication.text_preprocessor import clean_and_normalize_text
from ai_engine.communication.feature_extractor import extract_message_indicators
from ai_engine.communication.risk_assessor import calculate_communication_risk
from ai_engine.utils.logging import logger

BASE_DIR = Path(__file__).resolve().parent.parent
COMM_MODEL_DIR = BASE_DIR / "models" / "communication"
MODEL_FILENAME = "communication_fraud_classifier.joblib"
METADATA_FILENAME = "model_metadata.json"


class CommunicationDetector:
    """
    Modular detector for suspicious SMS, WhatsApp, Email, and Digital Arrest scams.
    """

    def __init__(self):
        self._pipeline = None
        self._metadata = None
        self._is_loaded = False
        self._load_error = None
        self._load_model()

    def _load_model(self):
        model_path = COMM_MODEL_DIR / MODEL_FILENAME
        meta_path = COMM_MODEL_DIR / METADATA_FILENAME

        if not model_path.exists():
            self._load_error = f"Model artifact not found at {model_path}. Model training required."
            return

        try:
            self._pipeline = joblib.load(model_path)
            if meta_path.exists():
                with open(meta_path, "r", encoding="utf-8") as f:
                    self._metadata = json.load(f)
            else:
                self._metadata = {"model_version": "v1.0.0"}
            self._is_loaded = True
            self._load_error = None
            logger.info("Stage 3 Communication Fraud Model loaded successfully.")
        except Exception as e:
            self._load_error = str(e)
            self._is_loaded = False
            logger.error(f"Failed to load communication model: {e}")

    def get_status(self) -> Dict[str, Any]:
        """Returns live detector status, version, and independent metrics."""
        return {
            "model_available": (COMM_MODEL_DIR / MODEL_FILENAME).exists(),
            "model_loaded": self._is_loaded,
            "model_version": self._metadata.get("model_version", "none") if self._metadata else "none",
            "algorithm": self._metadata.get("algorithm", "none") if self._metadata else "none",
            "engine_stage": "Stage 3: Intelligent Communication Fraud Detection",
            "training_status": "TRAINED" if self._is_loaded else "NEEDS_TRAINING",
            "inference_status": "READY" if self._is_loaded else "UNAVAILABLE",
            "metrics_summary": self._metadata.get("test_metrics", {}) if self._metadata else {},
            "load_error": self._load_error
        }

    def analyze_message(self, raw_message: str) -> Dict[str, Any]:
        """
        Processes message string with NLP pipeline + heuristic indicator evaluation.
        """
        start_time = time.perf_counter()

        if not self._is_loaded:
            self._load_model()

        cleaned_text = clean_and_normalize_text(raw_message)
        if not cleaned_text:
            return {
                "success": False,
                "classification": "INVALID",
                "risk_level": "UNKNOWN",
                "risk_score": 0.0,
                "confidence": 0.0,
                "detected_indicators": ["Empty or invalid message string."],
                "explanation": "No text content was provided for analysis.",
                "recommendations": ["Submit a valid message string containing words or phrases."],
                "model_version": self._metadata.get("model_version", "v1.0.0") if self._metadata else "none",
                "analysis": {
                    "latency_ms": 0.0,
                    "model_algorithm": "none",
                    "indicators_breakdown": {}
                }
            }

        # 1. Linguistic & Heuristic Indicator Extraction
        indicators_meta = extract_message_indicators(cleaned_text)

        # 2. Machine Learning Model Inference
        model_prob = 0.0
        confidence = 0.5
        algorithm_name = "Heuristic_Fallback"

        if self._is_loaded and self._pipeline:
            algorithm_name = self._metadata.get("algorithm", "LinearSVC")
            try:
                # LinearSVC decision function calibrated via sigmoid approximation
                if hasattr(self._pipeline.named_steps["clf"], "decision_function"):
                    decision = self._pipeline.decision_function([cleaned_text])[0]
                    # Sigmoid transform: 1 / (1 + exp(-x))
                    model_prob = float(1.0 / (1.0 + np.exp(-decision)))
                elif hasattr(self._pipeline, "predict_proba"):
                    probs = self._pipeline.predict_proba([cleaned_text])[0]
                    model_prob = float(probs[1])
                else:
                    pred = self._pipeline.predict([cleaned_text])[0]
                    model_prob = 1.0 if pred == 1 else 0.0

                confidence = round(max(model_prob, 1.0 - model_prob), 4)
            except Exception as e:
                logger.error(f"Inference error on text: {e}")
                model_prob = 0.5

        # 3. Explainable Multi-Factor Risk Assessment
        risk_score, classification, risk_level, explanation, recommendations = calculate_communication_risk(
            model_fraud_prob=model_prob,
            indicators_meta=indicators_meta
        )

        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)

        return {
            "success": True,
            "classification": classification,
            "risk_level": risk_level,
            "risk_score": risk_score,
            "confidence": confidence,
            "detected_indicators": indicators_meta["detected_indicators"],
            "explanation": explanation,
            "recommendations": recommendations,
            "model_version": self._metadata.get("model_version", "v1.0.0-tfidf-linear-svc") if self._metadata else "v1.0.0",
            "analysis": {
                "latency_ms": latency_ms,
                "model_algorithm": algorithm_name,
                "ml_fraud_probability": round(model_prob, 4),
                "indicators_breakdown": {
                    "urgency_markers": indicators_meta["urgency_count"],
                    "financial_markers": indicators_meta["financial_count"],
                    "impersonation_markers": indicators_meta["impersonation_count"],
                    "social_engineering_markers": indicators_meta["social_eng_count"],
                    "digital_arrest_markers": indicators_meta["digital_arrest_count"]
                },
                "is_digital_arrest_candidate": indicators_meta["is_digital_arrest_candidate"]
            }
        }


communication_detector = CommunicationDetector()

