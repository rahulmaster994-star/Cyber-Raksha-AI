"""
Cyber Raksha AI - Base Preprocessor Interface
"""
from abc import ABC, abstractmethod
from typing import Any


class BasePreprocessor(ABC):
    """Abstract Base Class for all future AI input preprocessors."""

    @abstractmethod
    def preprocess(self, raw_input: Any) -> Any:
        """Transforms raw incoming data (text, URL, audio) into model-ready tensors or vectors."""
        pass
