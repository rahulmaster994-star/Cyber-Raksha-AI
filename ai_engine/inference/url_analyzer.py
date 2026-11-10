"""
Cyber Raksha AI - Structural URL Analyzer
Exposes direct lexical breakdown and heuristic risk inspection.
"""
from typing import Dict, Any, List
from ai_engine.core.feature_extraction import extract_url_features, identify_risk_indicators
from ai_engine.utils.validation import validate_url


def analyze_url_structure(url: str) -> Dict[str, Any]:
    """
    Parses and extracts URL characteristics without invoking model weights.
    Useful for lightweight heuristic audits.
    """
    is_valid, normalized, err = validate_url(url)
    if not is_valid:
        return {"is_valid": False, "error": err, "features": {}, "indicators": []}

    features = extract_url_features(normalized)
    indicators = identify_risk_indicators(features, normalized)

    return {
        "is_valid": True,
        "normalized_url": normalized,
        "features": features,
        "risk_indicators": indicators
    }
