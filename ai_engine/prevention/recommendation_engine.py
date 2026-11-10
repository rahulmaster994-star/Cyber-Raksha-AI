"""
recommendation_engine.py — Stage 6
Generates tailored, prioritized prevention recommendations
based strictly on genuine detection evidence.
"""
from typing import Dict, Any, List, Optional


def generate_recommendations(
    classification: str,
    risk_level: str,
    risk_score: float,
    threat_category: Optional[str] = None,
    detected_indicators: Optional[List[str]] = None,
    threat_intel_matches: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Produces prioritized action plans categorized into:
      - immediate_actions (high priority, zero-delay mitigations)
      - short_term_actions (within 24 hours containment)
      - long_term_prevention (hygiene & policies)
      - reporting_guidance (official portals & helplines)
    """
    immediate: List[Dict[str, str]] = []
    short_term: List[Dict[str, str]] = []
    long_term: List[Dict[str, str]] = []
    reporting: List[Dict[str, str]] = []

    c_upper = (classification or "").upper()
    cat_upper = (threat_category or "").upper()
    indicators = detected_indicators or []
    intel = threat_intel_matches or []

    # 1. Phishing & Malicious URLs
    if "PHISHING" in c_upper or "PHISHING" in cat_upper or any("URL" in ind for ind in indicators):
        immediate.append({
            "action": "DO_NOT_SUBMIT_CREDENTIALS",
            "title": "Never Enter Passwords or OTPs",
            "reason": "This link exhibits structural and lexical signatures of an unauthorized harvesting page."
        })
        immediate.append({
            "action": "CLOSE_BROWSER_TAB",
            "title": "Close the Web Page Immediately",
            "reason": "Prevents drive-by script execution or credential theft."
        })
        short_term.append({
            "action": "VERIFY_DOMAIN_REGISTRY",
            "title": "Compare with Legitimate Institution Domain",
            "reason": "Official banking and portal sites use authentic root domains (e.g., sbi.co.in, hdfcbank.com)."
        })
        long_term.append({
            "action": "ENABLE_FIDO2_OR_APP_MFA",
            "title": "Implement Phishing-Resistant MFA",
            "reason": "FIDO2 security keys and Authenticator apps cannot be intercepted by fake reverse proxies."
        })
        reporting.append({
            "action": "REPORT_CHAKSHU",
            "title": "Report to DoT Sanchar Saathi (Chakshu)",
            "portal": "https://sancharsaathi.gov.in/sfc",
            "reason": "Assists Indian authorities in taking down fraudulent telecom connections and servers."
        })

    # 2. Digital Arrest & Fake Authority Coercion
    if "DIGITAL_ARREST" in c_upper or "DIGITAL_ARREST" in cat_upper:
        immediate.append({
            "action": "DISCONNECT_VIDEO_CALL",
            "title": "Immediately Terminate Video & Audio Calls",
            "reason": "Indian Law Enforcement agencies (CBI, Police, ED) NEVER conduct court proceedings or arrest citizens over WhatsApp/Skype."
        })
        immediate.append({
            "action": "REFUSE_FUND_TRANSFER",
            "title": "Do Not Transfer Money to Any Account or UPI",
            "reason": "Government agencies never require 'clearance deposits' to verify innocence or unfreeze accounts."
        })
        short_term.append({
            "action": "CONTACT_NEAREST_POLICE",
            "title": "Visit Your Nearest Local Police Station",
            "reason": "Verify genuine police inquiries in person without third-party telephonic intermediaries."
        })
        reporting.append({
            "action": "DIAL_1930",
            "title": "Call Cybercrime Helpline 1930",
            "portal": "https://cybercrime.gov.in",
            "reason": "Report active extortion attempts to the Ministry of Home Affairs I4C national registry."
        })

    # 3. Voice Cloning & Audio Deepfakes
    if "VOICE" in c_upper or "VOICE" in cat_upper or "DEEPFAKE" in c_upper:
        immediate.append({
            "action": "OUT_OF_BAND_VERIFICATION",
            "title": "Call Back on Known Verified Offline Number",
            "reason": "Modern zero-shot AI voice cloning can mimic voice timbre; confirm identity through a trusted alternative contact channel."
        })
        immediate.append({
            "action": "HALT_FINANCIAL_TRANSACTIONS",
            "title": "Halt Emergency Transfers",
            "reason": "Scammers frequently clone voices of executives or distressed family members requesting urgent wire transfers."
        })
        short_term.append({
            "action": "VERIFY_WITH_CODENAME",
            "title": "Challenge with Private Personal Trivia",
            "reason": "Ask a private question that generative AI models and scraped public data cannot answer."
        })

    # 4. Threat Intel Feed Matches
    if intel:
        immediate.append({
            "action": "BLOCK_INDICATOR_AT_FIREWALL",
            "title": f"Block Threat Indicator ({intel[0].get('source_name', 'Verified Feed')})",
            "reason": "This target has been independently reported on active cybersecurity threat feeds."
        })

    # Default fallback if low risk
    if not immediate:
        immediate.append({
            "action": "MAINTAIN_VIGILANCE",
            "title": "Standard Cyber Hygiene",
            "reason": "No active threat signatures detected; continue exercising normal cybersecurity awareness."
        })

    return {
        "classification": classification,
        "risk_level": risk_level,
        "risk_score": risk_score,
        "immediate_actions": immediate,
        "short_term_actions": short_term,
        "long_term_prevention": long_term,
        "reporting_guidance": reporting
    }

