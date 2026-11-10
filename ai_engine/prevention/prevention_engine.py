"""
prevention_engine.py — Stage 6
Central prevention coordinator tying together recommendation engines,
response playbooks, and recovery assistants.
"""
from typing import Dict, Any, List, Optional
from ai_engine.prevention.recommendation_engine import generate_recommendations
from ai_engine.prevention.protection_rules import RESPONSE_PLAYBOOKS, OFFICIAL_CONTACTS
from ai_engine.prevention.recovery_assistant import RecoveryAssistant


class PreventionEngine:
    def get_playbooks(self) -> List[Dict[str, Any]]:
        """Return all available guided incident response playbooks."""
        return list(RESPONSE_PLAYBOOKS.values())

    def get_playbook_by_id(self, playbook_id: str) -> Optional[Dict[str, Any]]:
        for pb in RESPONSE_PLAYBOOKS.values():
            if pb.get("id") == playbook_id:
                return pb
        return None

    def create_recommendations(
        self,
        classification: str,
        risk_level: str,
        risk_score: float,
        threat_category: Optional[str] = None,
        detected_indicators: Optional[List[str]] = None,
        threat_intel_matches: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        return generate_recommendations(
            classification=classification,
            risk_level=risk_level,
            risk_score=risk_score,
            threat_category=threat_category,
            detected_indicators=detected_indicators,
            threat_intel_matches=threat_intel_matches
        )

    def ask_assistant(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return RecoveryAssistant.answer_query(query, context)


prevention_engine = PreventionEngine()

