"""
risk_assessor.py — Stage 4
Combines ML classifier probability and acoustic spectral indicators
into a unified, calibrated risk score, classification, and actionable report.

Classification Categories:
  - LIKELY_NATURAL:            Score < 35, low probability of AI generation
  - INCONCLUSIVE:               Audio quality too low or conflicting signals
  - POSSIBLY_MANIPULATED:       Score 35-59, moderate synthetic indicators detected
  - POTENTIALLY_AI_GENERATED:   Score 60-79, strong neural TTS / vocoder patterns
  - POTENTIALLY_VOICE_CLONED:   Score >= 80, high confidence synthetic voice cloning

IMPORTANT: Per Stage 4 requirements:
  - Do NOT claim 100% deepfake detection accuracy
  - Do NOT claim a voice is genuine just because no synthetic indicators were detected
  - Clearly report acoustic limitations
"""
from typing import Dict, List, Tuple


def assess_audio_risk(
    ml_probability: float,
    acoustic_indicators: List[Dict],
    spectral_metrics: Dict,
    audio_metadata: Dict,
) -> Dict:
    """
    Combine ML probability and acoustic indicators to produce risk assessment.

    Args:
        ml_probability: float in [0.0, 1.0] from trained classifier
        acoustic_indicators: list of indicator dicts from spectrogram_analyzer
        spectral_metrics: dict of spectral statistics
        audio_metadata: dict of audio file properties

    Returns:
        Structured risk assessment dictionary.
    """
    # 1. Compute indicator score (capped at 40 points)
    indicator_weight_total = sum(ind.get("score_weight", 10) for ind in acoustic_indicators)
    indicator_score = min(40.0, float(indicator_weight_total))

    # 2. ML score (up to 60 points)
    ml_score = ml_probability * 60.0

    # 3. Combined score
    raw_score = ml_score + indicator_score
    risk_score = round(min(100.0, max(0.0, raw_score)), 1)

    # 4. Check for INCONCLUSIVE edge cases
    duration = audio_metadata.get("duration_seconds", 0.0)
    is_inconclusive = False
    inconclusive_reason = None

    if duration < 0.8:
        is_inconclusive = True
        inconclusive_reason = "Audio sample is very short (<0.8s); insufficient phonetic variety for reliable detection."
    elif audio_metadata.get("channels", 1) == 0:
        is_inconclusive = True
        inconclusive_reason = "Audio channel data is invalid."

    # 5. Classify
    if is_inconclusive:
        classification = "INCONCLUSIVE"
        risk_level = "LOW"
        risk_score = min(risk_score, 30.0)
    elif risk_score >= 80.0:
        classification = "POTENTIALLY_VOICE_CLONED"
        risk_level = "CRITICAL"
    elif risk_score >= 60.0:
        classification = "POTENTIALLY_AI_GENERATED"
        risk_level = "HIGH"
    elif risk_score >= 35.0:
        classification = "POSSIBLY_MANIPULATED"
        risk_level = "MEDIUM"
    else:
        classification = "LIKELY_NATURAL"
        risk_level = "LOW"

    # Confidence calculation: distance from decision boundary (0.50)
    confidence = round(abs(ml_probability - 0.5) * 2.0, 3)

    # 6. Generate explanation
    explanation = _build_explanation(
        classification,
        risk_score,
        ml_probability,
        acoustic_indicators,
        is_inconclusive,
        inconclusive_reason,
    )

    # 7. Generate actionable recommendations
    recommendations = _build_recommendations(classification, risk_level)

    return {
        "classification": classification,
        "risk_level": risk_level,
        "risk_score": risk_score,
        "confidence": confidence,
        "ml_probability": round(ml_probability, 4),
        "indicator_score": indicator_score,
        "indicators_count": len(acoustic_indicators),
        "detected_indicators": acoustic_indicators,
        "spectral_metrics": spectral_metrics,
        "audio_metadata": audio_metadata,
        "explanation": explanation,
        "recommendations": recommendations,
        "is_inconclusive": is_inconclusive,
        "inconclusive_reason": inconclusive_reason,
    }


def _build_explanation(
    classification: str,
    risk_score: float,
    ml_probability: float,
    indicators: List[Dict],
    is_inconclusive: bool,
    inconclusive_reason: str = None,
) -> str:
    if is_inconclusive:
        return (
            f"Analysis is INCONCLUSIVE: {inconclusive_reason} "
            "A longer, clear speech recording (2–10 seconds) is recommended for conclusive results. "
            "This result cannot confirm whether the voice is natural or synthetic."
        )

    parts = []
    if classification == "POTENTIALLY_VOICE_CLONED":
        parts.append(
            f"HIGH RISK (Score: {risk_score}/100): Strong acoustic and machine-learning indicators "
            f"suggest this audio recording contains synthetic speech characteristic of AI voice cloning. "
            f"The ML model evaluated synthetic probability at {ml_probability * 100:.1f}%."
        )
    elif classification == "POTENTIALLY_AI_GENERATED":
        parts.append(
            f"ELEVATED RISK (Score: {risk_score}/100): Noticeable synthetic speech signatures detected. "
            f"The voice exhibits vocoder artifacts and spectral regularity consistent with text-to-speech engines. "
            f"ML model estimated synthetic probability at {ml_probability * 100:.1f}%."
        )
    elif classification == "POSSIBLY_MANIPULATED":
        parts.append(
            f"MODERATE RISK (Score: {risk_score}/100): Some acoustic irregularities were identified. "
            "These may reflect audio compression, re-encoding, or subtle manipulation rather than "
            "a complete deepfake. Secondary verification is recommended."
        )
    else:
        parts.append(
            f"LOW RISK (Score: {risk_score}/100): Acoustic characteristics align with natural human speech. "
            "Natural pitch variation, harmonic structure, and ambient noise variability are consistent with "
            "an authentic recording. NOTE: Modern zero-shot voice clones can closely mimic human speech; "
            "always verify the caller's identity through an independent out-of-band channel."
        )

    if indicators:
        ind_names = [f"'{ind['name']}'" for ind in indicators]
        parts.append(f"Key detected indicators: {', '.join(ind_names)}.")

    return " ".join(parts)


def _build_recommendations(classification: str, risk_level: str) -> List[str]:
    recs = []

    if classification in ("POTENTIALLY_VOICE_CLONED", "POTENTIALLY_AI_GENERATED"):
        recs.append("DO NOT transfer funds, share OTPs, or disclose confidential credentials based on this call/message.")
        recs.append("HANG UP immediately and call the purported person or institution back on a known, verified number.")
        recs.append("Ask a 'shared secret' question that only the real individual would know (e.g., family trivia).")
        recs.append("If impersonating law enforcement or government officials, report to National Cyber Crime Portal (1930 / cybercrime.gov.in).")
        recs.append("Preserve the audio file as evidence — do not delete the recording.")
    elif classification == "POSSIBLY_MANIPULATED":
        recs.append("Verify the caller's identity using a known telephone number before taking any action.")
        recs.append("Request a video call with natural interaction (e.g., ask them to wave or turn their head).")
        recs.append("Be cautious if the call carries unexpected urgency, legal threats, or financial requests.")
    else:
        recs.append("Audio appears natural, but remain vigilant if financial or sensitive requests are involved.")
        recs.append("Never share OTPs, passwords, or personal banking information over the telephone.")
        recs.append("If received from an unknown sender, confirm authenticity via a secondary contact channel.")

    return recs

