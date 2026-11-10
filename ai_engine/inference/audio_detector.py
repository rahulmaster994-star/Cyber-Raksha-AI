"""
audio_detector.py — Stage 4
High-level inference engine for audio impersonation and synthetic voice detection.
Integrates validation, preprocessing, feature extraction, ML classification,
spectrogram analysis, and risk assessment into a unified pipeline.
"""
from pathlib import Path
from typing import Dict, Any, Optional
import json
import joblib
import numpy as np

from ai_engine.audio.audio_validator import validate_audio_file, AudioValidationError
from ai_engine.audio.audio_preprocessor import (
    load_and_preprocess,
    get_audio_metadata_from_bytes,
    AudioPreprocessingError
)
from ai_engine.audio.feature_extractor import extract_features
from ai_engine.audio.spectrogram_analyzer import analyze_spectrogram
from ai_engine.audio.risk_assessor import assess_audio_risk

MODEL_DIR = Path(__file__).resolve().parent.parent / "models" / "audio"
MODEL_PATH = MODEL_DIR / "voice_deepfake_detector.joblib"
METADATA_PATH = MODEL_DIR / "model_metadata.json"


class AudioDetector:
    """
    Inference orchestrator for Stage 4 Audio Detection.
    Singleton-friendly with lazy model loading.
    """

    def __init__(self):
        self.model = None
        self.feature_names = []
        self.metadata = {}
        self.is_loaded = False
        self._load_model()

    def _load_model(self) -> bool:
        """Load trained model and feature mapping if available."""
        if MODEL_PATH.exists():
            try:
                bundle = joblib.load(MODEL_PATH)
                self.model = bundle["model"]
                self.feature_names = bundle["feature_names"]
                if METADATA_PATH.exists():
                    with open(METADATA_PATH, "r", encoding="utf-8") as f:
                        self.metadata = json.load(f)
                self.is_loaded = True
                return True
            except Exception as e:
                print(f"[AudioDetector] Warning: Failed to load model: {e}")
                self.is_loaded = False
                return False
        return False

    def get_status(self) -> Dict[str, Any]:
        """Return engine status and telemetry."""
        if not self.is_loaded:
            self._load_model()

        return {
            "module": "VOICE_DETECT",
            "model_available": MODEL_PATH.exists(),
            "model_loaded": self.is_loaded,
            "model_name": self.metadata.get("model_name", "voice_deepfake_detector"),
            "model_type": self.metadata.get("model_type", "RandomForestClassifier"),
            "stage": "STAGE_4",
            "accuracy": self.metadata.get("metrics", {}).get("test_accuracy"),
            "features_count": len(self.feature_names),
            "supported_formats": [".wav"],
            "disclaimer": (
                "Deepfake audio detection provides probabilistic indicators. "
                "No audio detector can guarantee 100% accuracy. Always verify sensitive actions out-of-band."
            )
        }

    def analyze_audio(
        self,
        file_bytes: bytes,
        filename: str = "upload.wav",
        content_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze audio bytes for AI voice cloning and synthetic indicators.
        """
        # 1. Validation
        ext, file_size = validate_audio_file(file_bytes, filename)

        # 2. Extract quick metadata for summary
        quick_meta = get_audio_metadata_from_bytes(file_bytes, filename, file_size)

        # 3. Preprocess audio
        samples, sr, duration, detailed_meta = load_and_preprocess(file_bytes)
        quick_meta["duration_seconds"] = round(duration, 3)

        # 4. Feature Extraction (MFCC, spectral, temporal, pitch)
        features_dict = extract_features(samples, sr)

        # 5. Acoustic & Spectrogram Artifacts Analysis
        acoustic_indicators, spectral_metrics = analyze_spectrogram(samples, sr)

        # 6. ML Model Inference
        ml_prob = 0.5  # Neutral fallback if model not loaded
        if not self.is_loaded:
            self._load_model()

        if self.is_loaded and self.model is not None:
            # Construct aligned feature vector
            feature_vector = np.array(
                [[features_dict.get(fname, 0.0) for fname in self.feature_names]],
                dtype=np.float32
            )
            try:
                # Class 1 is Synthetic / AI Voice
                probs = self.model.predict_proba(feature_vector)[0]
                ml_prob = float(probs[1]) if len(probs) > 1 else float(probs[0])
            except Exception as e:
                print(f"[AudioDetector] Prediction error: {e}")
                ml_prob = 0.5

        # 7. Risk Assessment and Explanation Synthesis
        assessment = assess_audio_risk(
            ml_probability=ml_prob,
            acoustic_indicators=acoustic_indicators,
            spectral_metrics=spectral_metrics,
            audio_metadata=quick_meta
        )

        # 8. Enrich with engine info
        assessment["status"] = "SUCCESS"
        assessment["engine_version"] = "4.0.0"
        assessment["model_version"] = self.metadata.get("created_at", "v1.0")

        return assessment


# Global instance
audio_detector = AudioDetector()

