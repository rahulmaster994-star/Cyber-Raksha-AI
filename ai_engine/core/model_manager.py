"""
Cyber Raksha AI - Model Manager
Handles loading, caching, versioning, and validation of trained AI models.
"""
import json
import os
from typing import Optional, Tuple, Any, Dict
import joblib

from ai_engine.utils.config import (
    PHISHING_MODEL_DIR,
    MODEL_FILENAME,
    PREPROCESSOR_FILENAME,
    METADATA_FILENAME,
    CURRENT_MODEL_VERSION
)
from ai_engine.utils.logging import logger


class ModelManager:
    """
    Singleton manager for loading, verifying, and serving machine learning models.
    """

    def __init__(self):
        self._model: Optional[Any] = None
        self._preprocessor: Optional[Any] = None
        self._metadata: Optional[Dict[str, Any]] = None
        self._is_loaded: bool = False
        self._load_error: Optional[str] = None

    @property
    def model_path(self):
        return PHISHING_MODEL_DIR / MODEL_FILENAME

    @property
    def preprocessor_path(self):
        return PHISHING_MODEL_DIR / PREPROCESSOR_FILENAME

    @property
    def metadata_path(self):
        return PHISHING_MODEL_DIR / METADATA_FILENAME

    def is_model_available(self) -> bool:
        """Returns True only if the trained model artifact exists on disk."""
        return self.model_path.exists() and self.preprocessor_path.exists()

    def get_status(self) -> Dict[str, Any]:
        """Provides dynamic status of the model for health and system endpoints."""
        available = self.is_model_available()
        return {
            "model_available": available,
            "model_loaded": self._is_loaded,
            "model_version": self._metadata.get("model_version", CURRENT_MODEL_VERSION) if self._metadata else CURRENT_MODEL_VERSION,
            "algorithm": self._metadata.get("algorithm", "RandomForestClassifier") if self._metadata else "N/A",
            "training_status": "TRAINED" if available else "UNAVAILABLE / NEEDS TRAINING",
            "load_error": self._load_error
        }

    def load_model(self, force_reload: bool = False) -> Tuple[bool, str]:
        """
        Loads the trained model, preprocessor, and metadata into memory.
        """
        if self._is_loaded and not force_reload:
            return True, "Model already loaded in memory."

        if not self.is_model_available():
            self._load_error = f"Model artifact not found at {self.model_path}. Model must be trained first."
            self._is_loaded = False
            return False, self._load_error

        try:
            logger.info(f"Loading model artifacts from {PHISHING_MODEL_DIR}...")
            self._model = joblib.load(self.model_path)
            self._preprocessor = joblib.load(self.preprocessor_path)

            if self.metadata_path.exists():
                with open(self.metadata_path, "r", encoding="utf-8") as f:
                    self._metadata = json.load(f)
            else:
                self._metadata = {"model_version": CURRENT_MODEL_VERSION}

            self._is_loaded = True
            self._load_error = None
            logger.info("Phishing detection model loaded successfully.")
            return True, "Model loaded successfully."
        except Exception as e:
            self._load_error = f"Failed to load model: {str(e)}"
            self._is_loaded = False
            logger.error(self._load_error)
            return False, self._load_error

    def get_model(self) -> Optional[Any]:
        if not self._is_loaded:
            self.load_model()
        return self._model

    def get_preprocessor(self) -> Optional[Any]:
        if not self._is_loaded:
            self.load_model()
        return self._preprocessor

    def get_metadata(self) -> Dict[str, Any]:
        if not self._metadata:
            if self.metadata_path.exists():
                try:
                    with open(self.metadata_path, "r", encoding="utf-8") as f:
                        self._metadata = json.load(f)
                except Exception:
                    self._metadata = {}
            else:
                self._metadata = {}
        return self._metadata


model_manager = ModelManager()
