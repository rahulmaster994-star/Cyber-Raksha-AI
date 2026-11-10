"""
Cyber Raksha AI - Explainable Risk Assessment & Safety Guidance Engine
Combines ML text model predictions with domain-specific indicator signals
to compute transparent risk levels and security playbooks.
"""
from typing import Dict, Any, List, Tuple


def calculate_communication_risk(
    model_fraud_prob: float,
    indicators_meta: Dict[str, Any]
) -> Tuple[float, str, str, str, List[str]]:
    """
    Computes a transparent multi-factor risk score (0.0 to 100.0) combining:
    1. Supervised Machine Learning fraud probability (60% weight)
    2. Heuristic indicator presence across Urgency, Financial, Impersonation, Social Eng (40% weight)
    3. Severe escalation triggers for verified Digital Arrest scam combinations.

    Returns:
    (risk_score, classification, risk_level, explanation, recommendations)
    """
    ml_component = model_fraud_prob * 60.0

    total_indicators = indicators_meta.get("total_indicator_count", 0)
    digital_arrest_count = indicators_meta.get("digital_arrest_count", 0)
    is_da_candidate = indicators_meta.get("is_digital_arrest_candidate", False)

    # Heuristic component: up to 12 points per trigger, capped at 50
    heuristic_component = min(total_indicators * 12.0, 50.0)

    raw_score = ml_component + heuristic_component

    # Severe Digital Arrest escalation: If digital arrest patterns are present, minimum risk score is 85.0
    if is_da_candidate or digital_arrest_count >= 2:
        raw_score = max(raw_score, 88.0)

    # Coercive credential or impersonation escalation:
    if indicators_meta.get("financial_count", 0) >= 1 and indicators_meta.get("urgency_count", 0) >= 1:
        raw_score = max(raw_score, 75.0)

    if indicators_meta.get("impersonation_count", 0) >= 1 and indicators_meta.get("urgency_count", 0) >= 1:
        raw_score = max(raw_score, 68.0)

    risk_score = round(min(max(raw_score, 0.0), 100.0), 2)

    # Classification & Risk Level Decision Boundary
    recommendations: List[str] = []

    # Contextual & Negation Handling: Educational advisory messages
    if indicators_meta.get("is_educational_advisory", False):
        classification = "SAFE"
        risk_level = "LOW"
        risk_score = min(risk_score, 18.5)
        explanation = (
            "Educational security advisory detected: This message informs and warns citizens about fraudulent tactics, "
            "fake authority impersonation, or digital arrest scams rather than executing an attack."
        )
        recommendations = [
            "This message appears to be a legitimate awareness or warning notice.",
            "Continue following standard cybersecurity safety tips and never share sensitive credentials."
        ]
        return risk_score, classification, risk_level, explanation, recommendations

    if is_da_candidate or (digital_arrest_count >= 1 and (indicators_meta.get("impersonation_count", 0) > 0 or indicators_meta.get("financial_count", 0) > 0)):
        classification = "DIGITAL_ARREST_SCAM"
        risk_level = "CRITICAL"
        explanation = (
            "CRITICAL ALERT: Strong evidence of an organized Digital-Arrest scam. "
            "Scammers impersonate police, CBI, or judicial officials over phone/video calls, alleging criminal charges, "
            "fabricated arrest warrants, or Aadhaar misuse to coerce funds into 'safe accounts'."
        )
        recommendations = [
            "DO NOT join any Skype, WhatsApp, or video calls for interrogation or verification.",
            "Law enforcement agencies and courts NEVER conduct 'digital arrests' or video-call trials.",
            "NEVER transfer money to any 'government verification' or 'safe RBI' bank account.",
            "Immediately report this incident to the National Cybercrime Helpline at 1930 or cybercrime.gov.in.",
            "Discuss the situation with family or visit your local police station in person."
        ]

    elif indicators_meta.get("financial_count", 0) >= 2 or (indicators_meta.get("financial_count", 0) >= 1 and indicators_meta.get("urgency_count", 0) >= 1) or (indicators_meta.get("financial_count", 0) >= 1 and risk_score >= 65.0):
        classification = "FINANCIAL_SCAM"
        risk_level = "CRITICAL" if risk_score >= 85.0 else "HIGH"
        explanation = (
            "High probability of financial fraud or credential harvesting. The message attempts to coerce "
            "confidential OTPs, banking PINs, or urgent money transfers under the guise of an account crisis."
        )
        recommendations = [
            "NEVER disclose OTPs, UPI PINs, or internet banking passwords to anyone.",
            "Banks and financial institutions will NEVER ask for your password or OTP over SMS or phone.",
            "Verify account status directly through the bank's official mobile banking app or customer care.",
            "If funds were fraudulently debited, immediately dial 1930 to freeze transactions within the golden hour."
        ]

    elif indicators_meta.get("impersonation_count", 0) >= 1 and (indicators_meta.get("urgency_count", 0) >= 1 or risk_score >= 55.0):
        classification = "IMPERSONATION"
        risk_level = "HIGH"
        explanation = (
            "Suspicious authority impersonation detected. The communication claims to represent a government body, "
            "telecom regulator (TRAI), police, or courier service to induce panic or compliance."
        )
        recommendations = [
            "Independently verify the sender's identity using publicly listed official helpline numbers.",
            "Do not click on unverified links or download APK files sent via SMS or messaging apps.",
            "Official agencies do not issue disconnection or seizure threats over informal chat messages."
        ]

    elif risk_score >= 70.0 or model_fraud_prob >= 0.75:
        classification = "PHISHING"
        risk_level = "HIGH"
        explanation = (
            "The message exhibits deceptive linguistic indicators consistent with phishing campaigns or malicious spam."
        )
        recommendations = [
            "Do not click on any embedded links or attachments in this message.",
            "Block the sender and report the message as spam/phishing on your device.",
            "Do not call back any phone numbers listed in the message body."
        ]

    elif risk_score >= 45.0 or model_fraud_prob >= 0.45 or total_indicators >= 1:
        classification = "SUSPICIOUS"
        risk_level = "MEDIUM"
        explanation = (
            "Some abnormal urgency or unverified request patterns were observed. Evidence is insufficient to "
            "conclusively confirm fraud, but caution is warranted."
        )
        recommendations = [
            "Exercise caution before responding or sharing any personal details.",
            "Verify the authenticity of the sender through independent channels before taking action."
        ]

    elif model_fraud_prob < 0.20 and total_indicators == 0:
        classification = "SAFE"
        risk_level = "LOW"
        explanation = (
            "No significant indicators of fraud, impersonation, or social engineering were detected in this message. "
            "The content aligns with standard legitimate or non-coercive communication."
        )
        recommendations = [
            "Standard security hygiene applies. Continue verifying sensitive requests before sharing confidential information."
        ]

    else:
        classification = "INCONCLUSIVE"
        risk_level = "LOW"
        explanation = (
            "Inconclusive determination: The text does not contain sufficient diagnostic signals to definitively establish legitimacy or fraud."
        )
        recommendations = [
            "Evaluate the sender's identity through external verification before engaging in transactions."
        ]

    return risk_score, classification, risk_level, explanation, recommendations
