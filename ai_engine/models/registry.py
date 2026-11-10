"""
Cyber Raksha AI - Model Registry
Central catalog for registering and retrieving machine learning models.
"""
from typing import Dict, Any, Optional


class ModelRegistry:
    """Manages the lifecycle of AI models across Cyber Raksha AI modules."""

    def __init__(self):
        self._registry: Dict[str, Any] = {}

    def register(self, module_code: str, model_instance: Any) -> None:
        self._registry[module_code] = model_instance

    def get(self, module_code: str) -> Optional[Any]:
        return self._registry.get(module_code)

    def is_loaded(self, module_code: str) -> bool:
        return module_code in self._registry

    def list_loaded_models(self) -> list[str]:
        return list(self._registry.keys())


registry = ModelRegistry()
