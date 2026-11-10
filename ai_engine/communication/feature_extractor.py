"""
Cyber Raksha AI - Communication Linguistic & Heuristic Feature Extractor
Extracts multi-vector threat signals:
A. Urgency & Coercion
B. Financial & Credential Demands
C. Impersonation (Govt, Police, Banks)
D. Social Engineering Manipulation
E. Digital Arrest Signatures
"""
import re
from typing import Dict, Any, List


# --- Indicator Patterns ---
URGENCY_PATTERNS = [
    r'\b(?:immediately|urgent|urgently|within \d+ (?:hours?|minutes?)|right now|without delay)\b',
    r'\b(?:account (?:will be|has been) (?:blocked|suspended|frozen|deactivated|terminated))\b',
    r'\b(?:action required|immediate action|deadline|expire[sd]? today|last chance)\b',
    r'\b(?:final notice|warning|alert|critical notice)\b'
]

FINANCIAL_PATTERNS = [
    r'\b(?:otp|one[- ]time password|verification code|pin|cvv|secret code)\b',
    r'\b(?:share (?:your )?(?:otp|pin|password|credentials))\b',
    r'\b(?:transfer (?:funds|money|amount|rupees|inr|rs\.?|\$|\d+))\b',
    r'\b(?:bank account|credit card|debit card|net banking|upi id|payment link)\b',
    r'\b(?:gift card|crypto|bitcoin|usdt|telegram task|part[- ]time job|earn daily)\b',
    r'\b(?:refundable deposit|processing fee|security deposit|clearance charge|bill unpaid|power disconnected)\b'
]

IMPERSONATION_PATTERNS = [
    r'\b(?:cbi|central bureau of investigation|ed|enforcement directorate|police|cyber crime branch)\b',
    r'\b(?:mha|ministry of home affairs|trai|telecom regulatory|supreme court|high court|customs department)\b',
    r'\b(?:rbi|reserve bank|sbi|hdfc|icici|axis bank|bank manager|security department)\b',
    r'\b(?:fedex|dhl|courier department|customs officer|narcotics control bureau|ncb)\b',
    r'\b(?:customer care|support executive|helpdesk agent|tech support|fraud prevention officer)\b'
]

SOCIAL_ENGINEERING_PATTERNS = [
    r'\b(?:do not (?:tell|inform|share with) (?:anyone|family|police|lawyer))\b',
    r'\b(?:keep (?:this )?(?:confidential|secret|private))\b',
    r'\b(?:install (?:anydesk|teamviewer|rustdesk|quicksupport|remote desktop))\b',
    r'\b(?:click (?:on )?(?:this|the) (?:link|url|attachment)|download apk|update kyc)\b',
    r'\b(?:you have won|lottery|lucky draw|cash prize|reward points expire)\b',
    r'\b(?:compromised in money laundering|illegal parcel|narcotics found)\b'
]

DIGITAL_ARREST_PATTERNS = [
    r'\b(?:digital arrest|virtual arrest|custody over video)\b',
    r'\b(?:arrest warrant (?:issued|against you)|non[- ]bailable warrant)\b',
    r'\b(?:video call (?:interrogation|verification|investigation|statement))\b',
    r'\b(?:stay on (?:video call|skype|whatsapp video) until verification)\b',
    r'\b(?:aadhaar (?:card )?(?:linked to|misused in|involved in) (?:criminal activity|drugs|money laundering))\b',
    r'\b(?:transfer (?:funds|money) to (?:a |the )?(?:safe|rbi|government|verification) account)\b',
    r'\b(?:clear your name|prove your innocence|avoid immediate arrest)\b',
    r'\b(?:illegal contraband|drugs seized|sim card issued in your name used for terrorism)\b'
]

# Direct First-Person Coercive Action Patterns (Disqualifies educational claims)
DIRECT_COERCION_PATTERNS = [
    r'\b(?:i am (?:a |an )?(?:police|cbi|customs|inspector|dcp|officer|judge|rbi official))\b',
    r'\b(?:transfer (?:funds|money|\d+|rs|inr) (?:immediately|right now|to safe|to account|without delay))\b',
    r'\b(?:you (?:will be|are) (?:under arrest|arrested|detained|jailed|prosecuted))\b',
    r'\b(?:or you will (?:be arrested|face immediate arrest|go to jail))\b',
    r'\b(?:join (?:this |the )?(?:skype|video call|whatsapp video) (?:call|immediately|now))\b',
    r'\b(?:share (?:your )?(?:cancellation |verification )?(?:otp|pin|password))\b'
]

# Educational & Awareness Context Patterns (Third-party reporting, alerts, advice)
EDUCATIONAL_ADVISORY_PATTERNS = [
    r'\b(?:police (?:are|is) warning|cbi (?:is|are) warning|rbi (?:is|are) warning|authorities warn|banks? warn)\b',
    r'\b(?:cyber (?:safety|security) tip|security advisory|awareness (?:tip|alert|campaign))\b',
    r'\b(?:beware of (?:scammers?|fraudsters?|fake|cyber criminals?|calls))\b',
    r'\b(?:warning (?:people|citizens?|users?|public|about))\b',
    r'\b(?:scam alert|fraud awareness|public advisory|tips to (?:avoid|protect|prevent))\b',
    r'\b(?:seminar|lecture|demonstrat(?:ed?|ing)|study shows|educational (?:demonstration|alert))\b',
    r'\b(?:media report|press release|news alert|informational notice)\b'
]

# Semantic Negation Patterns (Negates coercion or fraudulent intent)
NEGATION_PATTERNS = [
    r'\b(?:law enforcement never|police never|cbi never|rbi never|banks? never|courts? never)\b',
    r'\b(?:never (?:conducts?|demands?|arrests?|asks? for|transfers?|shares?))\b',
    r'\b(?:do not (?:fall for|transfer|share your pin|trust unverified|click))\b',
    r'\b(?:scammers? (?:pretend|claim|fake|impersonate|use))\b',
    r'\b(?:fake (?:arrest|officials?|policeman|cbi|warrants?))\b'
]


def extract_message_indicators(text: str) -> Dict[str, Any]:
    """
    Extracts semantic threat markers across Urgency, Financial, Impersonation,
    Social Engineering, and Digital Arrest domains.
    """
    lower_text = text.lower()

    urgency_matches = []
    for pat in URGENCY_PATTERNS:
        if re.search(pat, lower_text):
            urgency_matches.append(pat)

    financial_matches = []
    for pat in FINANCIAL_PATTERNS:
        if re.search(pat, lower_text):
            financial_matches.append(pat)

    impersonation_matches = []
    for pat in IMPERSONATION_PATTERNS:
        if re.search(pat, lower_text):
            impersonation_matches.append(pat)

    social_eng_matches = []
    for pat in SOCIAL_ENGINEERING_PATTERNS:
        if re.search(pat, lower_text):
            social_eng_matches.append(pat)

    digital_arrest_matches = []
    for pat in DIGITAL_ARREST_PATTERNS:
        if re.search(pat, lower_text):
            digital_arrest_matches.append(pat)

    # Check for direct coercive calls to action (prohibits spoofed educational claims)
    direct_coercion_matches = []
    for pat in DIRECT_COERCION_PATTERNS:
        if re.search(pat, lower_text):
            direct_coercion_matches.append(pat)

    # Check for educational / advisory context & semantic negation
    educational_matches = []
    for pat in EDUCATIONAL_ADVISORY_PATTERNS:
        if re.search(pat, lower_text):
            educational_matches.append(pat)

    negation_matches = []
    for pat in NEGATION_PATTERNS:
        if re.search(pat, lower_text):
            negation_matches.append(pat)

    # Educational advisory is valid ONLY if protective context exists AND NO direct coercion demands are present
    is_educational_advisory = (
        len(educational_matches) > 0
        and len(negation_matches) > 0
        and len(direct_coercion_matches) == 0
    )

    # Human-readable detected indicator descriptions
    detected_indicators: List[str] = []

    if urgency_matches:
        detected_indicators.append(
            f"Artificial Urgency / Coercion Pressure detected ({len(urgency_matches)} markers)."
        )

    if financial_matches:
        detected_indicators.append(
            f"Financial Demands, OTP/PIN or payment solicitation detected ({len(financial_matches)} markers)."
        )

    if impersonation_matches:
        detected_indicators.append(
            f"Official Authority or Institutional Impersonation detected (Police/CBI/Bank/Regulator)."
        )

    if social_eng_matches:
        detected_indicators.append(
            f"Social Engineering / Isolation tactics detected (demands for secrecy or remote software installation)."
        )

    if digital_arrest_matches:
        detected_indicators.append(
            f"HIGH RISK DIGITAL ARREST signature detected (fabricated warrants, video interrogation or safe account transfers)."
        )

    if direct_coercion_matches:
        detected_indicators.append(
            f"Direct Coercive Demand detected ({len(direct_coercion_matches)} urgent call-to-action markers)."
        )

    return {
        "urgency_count": len(urgency_matches),
        "financial_count": len(financial_matches),
        "impersonation_count": len(impersonation_matches),
        "social_eng_count": len(social_eng_matches),
        "digital_arrest_count": len(digital_arrest_matches),
        "direct_coercion_count": len(direct_coercion_matches),
        "is_educational_advisory": is_educational_advisory,
        "educational_matches_count": len(educational_matches),
        "negation_matches_count": len(negation_matches),
        "total_indicator_count": (
            len(urgency_matches) + len(financial_matches) +
            len(impersonation_matches) + len(social_eng_matches) +
            len(digital_arrest_matches)
        ),
        "detected_indicators": detected_indicators,
        "is_digital_arrest_candidate": not is_educational_advisory and (
            len(digital_arrest_matches) >= 2 or (
                len(digital_arrest_matches) >= 1 and (len(impersonation_matches) >= 1 or len(urgency_matches) >= 1)
            )
        )
    }
