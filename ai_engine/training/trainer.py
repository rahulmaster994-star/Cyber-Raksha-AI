"""
Cyber Raksha AI - Base Trainer Interface
"""
from abc import ABC, abstractmethod
from typing import Any, Dict


class BaseTrainer(ABC):
    """Abstract Base Class for model training pipelines."""

    @abstractmethod
    def train(self, dataset: Any, config: Dict[str, Any]) -> Any:
        """Executes model training routine."""
        pass
