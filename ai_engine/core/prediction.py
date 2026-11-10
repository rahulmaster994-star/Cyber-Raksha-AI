"""
Cyber Raksha AI - Prediction Formats and Risk Scoring Logic
"""
from dataclasses import dataclass, asdict
from typing import Dict, Any, List, Tuple


@dataclass
class DetectionResult:
    success: bool
    url: str
    classification: str  # LEGITIMATE | PHISHING | SUSPICIOUS | INCONCLUSIVE
    risk_level: str      # LOW | MEDIUM | HIGH | CRITICAL
    risk_score: float    # 0.0 to 100.0
    model_version: str
    confidence: float    # 0.0 to 1.0
    analysis: Dict[str, Any]
    recommendation: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def calculate_risk_score(model_phishing_prob: float, risk_indicators: List[str]) -> Tuple[float, str, str, str]:
    """
    Computes a transparent, multi-factor risk score (0.0 - 100.0) combining:
    1. Supervised Machine Learning probability score (70% weight, calibrated against uncorroborated lexical overfitting)
    2. Explicit heuristic & behavioral indicators (30% weight)

    Defense-in-depth principles:
    - Never classify a URL as PHISHING solely on lexical length/hyphens when zero deceptive indicators exist.
    - Never automatically trust a domain solely on its TLD (.gov.in, etc.) if malicious indicators are present.
    """
    indicator_count = len(risk_indicators)
    heuristic_component = min(indicator_count * 10.0, 30.0)

    # When zero deceptive indicators exist, lexical model probability is calibrated
    # to avoid false positives on legitimate multi-hyphen or newly-registered business domains
    if indicator_count == 0:
        effective_ml_prob = min(model_phishing_prob, 0.25) if model_phishing_prob < 0.90 else min(model_phishing_prob * 0.25, 0.25)
        ml_component = effective_ml_prob * 70.0
    else:
        ml_component = model_phishing_prob * 70.0

    composite_score = round(ml_component + heuristic_component, 2)
    composite_score = min(max(composite_score, 0.0), 100.0)

    # Classification logic based on corroborated evidence:
    if composite_score >= 75.0 and indicator_count >= 1:
        classification = "PHISHING"
        risk_level = "CRITICAL" if composite_score >= 90.0 else "HIGH"
        recommendation = "CRITICAL WARNING: High probability of phishing or credential harvesting attack. DO NOT visit this link, enter passwords, or provide payment details."
    elif composite_score >= 45.0 or (indicator_count >= 1 and model_phishing_prob >= 0.50):
        classification = "SUSPICIOUS"
        risk_level = "HIGH" if composite_score >= 70.0 else "MEDIUM"
        recommendation = "SUSPICIOUS URL: Structural characteristics match known deception patterns. Verify the sender identity through an alternative channel."
    elif 0.45 <= model_phishing_prob <= 0.65 and indicator_count == 0:
        classification = "INCONCLUSIVE"
        risk_level = "LOW"
        recommendation = "Inconclusive determination: The URL does not exhibit clear indicators of phishing or known legitimacy. Exercise standard caution before entering credentials."
    else:
        classification = "LEGITIMATE"
        risk_level = "LOW"
        recommendation = "Low threat probability. Structural and lexical attributes align with standard legitimate web services. Always check browser SSL locks before submitting credentials."

    return composite_score, classification, risk_level, recommendation


class Tuple_Risk:
    pass
