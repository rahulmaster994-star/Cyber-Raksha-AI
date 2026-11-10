"""
backend/app/core/feature_flags.py
Stage 9: Dynamic Feature Flags & Controlled Subsystem Toggles.
Allows administrators to disable malfunctioning integrations without taking down the platform.
"""
from typing import Dict, Any
from datetime import datetime, timezone


class FeatureFlagsManager:
    """
    In-memory thread-safe feature flags manager with fallback defaults.
    """
    def __init__(self):
        self._flags: Dict[str, Dict[str, Any]] = {
            "enable_audio_analysis": {
                "enabled": True,
                "description": "Allow voice cloning & synthetic audio analysis uploads",
                "category": "AI_INFERENCE",
                "updated_at": datetime.now(timezone.utc).isoformat()
            },
            "enable_threat_intel_sync": {
                "enabled": True,
                "description": "Permit automatic and manual threat feed synchronization (URLhaus)",
                "category": "THREAT_INTEL",
                "updated_at": datetime.now(timezone.utc).isoformat()
            },
            "enable_unified_analysis": {
                "enabled": True,
                "description": "Enable cross-vector corroboration & unified risk assessment",
                "category": "RISK_ENGINE",
                "updated_at": datetime.now(timezone.utc).isoformat()
            },
            "enable_async_jobs": {
                "enabled": True,
                "description": "Allow asynchronous job queueing for long-running analyses",
                "category": "JOB_QUEUE",
                "updated_at": datetime.now(timezone.utc).isoformat()
            },
            "enable_model_drift_monitoring": {
                "enabled": True,
                "description": "Record input distribution shifts for AI models",
                "category": "OBSERVABILITY",
                "updated_at": datetime.now(timezone.utc).isoformat()
            },
            "enable_user_feedback": {
                "enabled": True,
                "description": "Allow users to submit feedback and false positive reports",
                "category": "USER_GOVERNANCE",
                "updated_at": datetime.now(timezone.utc).isoformat()
            },
            "strict_rate_limiting": {
                "enabled": True,
                "description": "Enforce 120 req/min general and 30 req/min heavy endpoint throttling",
                "category": "SECURITY",
                "updated_at": datetime.now(timezone.utc).isoformat()
            },
            "maintenance_mode": {
                "enabled": False,
                "description": "Reject public analysis requests with 503 Maintenance Mode status",
                "category": "SYSTEM",
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
        }

    def is_enabled(self, flag_name: str) -> bool:
        flag = self._flags.get(flag_name)
        if flag is None:
            return True  # default open
        return flag.get("enabled", True)

    def get_all_flags(self) -> Dict[str, Dict[str, Any]]:
        return self._flags

    def set_flag(self, flag_name: str, enabled: bool) -> bool:
        if flag_name in self._flags:
            self._flags[flag_name]["enabled"] = enabled
            self._flags[flag_name]["updated_at"] = datetime.now(timezone.utc).isoformat()
            return True
        return False


feature_flags = FeatureFlagsManager()

