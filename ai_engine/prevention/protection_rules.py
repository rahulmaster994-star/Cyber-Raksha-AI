"""
protection_rules.py — Stage 6
Comprehensive evidence-grounded incident response playbooks,
mitigation workflows, and official Indian reporting guidance.
"""
from typing import Dict, Any, List

# Official India-specific and international cybersecurity emergency channels
OFFICIAL_CONTACTS = {
    "INDIA_CYBERCRIME_PORTAL": "https://cybercrime.gov.in",
    "INDIA_CYBER_HELPLINE": "1930",
    "CERT_IN_INCIDENT_REPORT": "https://www.cert-in.org.in",
    "RBI_Sachet_PORTAL": "https://sachet.rbi.org.in",
    "CHAKSHU_SUSPICIOUS_COMM": "https://sancharsaathi.gov.in/sfc"
}

# Guided Incident Response Playbooks
RESPONSE_PLAYBOOKS: Dict[str, Dict[str, Any]] = {
    "PHISHING_CLICKED": {
        "id": "PLAYBOOK_PHISHING_LINK",
        "category": "Phishing Attack",
        "title": "Phishing Link Clicked or Visited",
        "description": "Step-by-step containment when a user accidentally clicks or visits an identified malicious URL.",
        "steps": [
            {
                "step_number": 1,
                "action_key": "CLOSE_PAGE_DISCONNECT",
                "title": "Immediately Close Suspicious Tab & Disconnect Network",
                "priority": "IMMEDIATE",
                "description": "Terminate the browser tab running the suspicious URL. If malware download was initiated, disconnect Wi-Fi to stop lateral traffic.",
                "is_user_confirmation_required": True
            },
            {
                "step_number": 2,
                "action_key": "PASSWORD_RESET_OFFICIAL",
                "title": "Reset Credentials Directly on Official Domain",
                "priority": "IMMEDIATE",
                "description": "If you typed any password, open a fresh browser window, navigate manually to the legitimate banking or email website, and reset your password immediately.",
                "is_user_confirmation_required": True
            },
            {
                "step_number": 3,
                "action_key": "ENABLE_HARDWARE_OR_TOTP_MFA",
                "title": "Enable Multi-Factor Authentication (MFA)",
                "priority": "SHORT_TERM",
                "description": "Activate Authenticator app-based OTPs or FIDO2 hardware keys. Avoid SMS-only verification where possible.",
                "is_user_confirmation_required": True
            },
            {
                "step_number": 4,
                "action_key": "REPORT_PHISH_PORTAL",
                "title": "Report Malicious URL to Sanchar Saathi / Chakshu",
                "priority": "LONG_TERM",
                "description": "Submit the phishing link to the DoT Chakshu portal (sancharsaathi.gov.in) to flag the sender's SIM and domain across Indian telecom providers.",
                "is_user_confirmation_required": False
            }
        ]
    },
    "MONEY_TRANSFERRED_SCAM": {
        "id": "PLAYBOOK_FINANCIAL_FRAUD",
        "category": "Financial Fraud",
        "title": "Money Transferred to Fraudulent Account / UPI",
        "description": "Emergency recovery workflow when funds have been transferred under coercion, fake KYC, or deception.",
        "steps": [
            {
                "step_number": 1,
                "action_key": "CALL_1930_GOLDEN_HOUR",
                "title": "Call National Cyber Crime Helpline 1930 (Golden Hour)",
                "priority": "IMMEDIATE",
                "description": "Report the fraudulent transaction immediately to 1930 or submit at cybercrime.gov.in within 2 hours to freeze funds in transit across the banking switch.",
                "is_user_confirmation_required": True
            },
            {
                "step_number": 2,
                "action_key": "FREEZE_BANK_ACCOUNT_UPI",
                "title": "Contact Your Bank to Block UPI & Card Immediately",
                "priority": "IMMEDIATE",
                "description": "Call your bank's 24x7 toll-free fraud number to freeze your UPI VPA, net-banking account, and debit/credit cards.",
                "is_user_confirmation_required": True
            },
            {
                "step_number": 3,
                "action_key": "PRESERVE_TRANSACTION_EVIDENCE",
                "title": "Save UTR Numbers, Screenshots & Call Logs",
                "priority": "SHORT_TERM",
                "description": "Record the UPI Transaction Reference (UTR) number, destination account/VPA, extortion chat screenshots, and phone call timestamps as legal evidence.",
                "is_user_confirmation_required": True
            },
            {
                "step_number": 4,
                "action_key": "LODGE_FORMAL_FIR",
                "title": "File Formal Incident Complaint at cybercrime.gov.in",
                "priority": "SHORT_TERM",
                "description": "Upload preserved evidence on cybercrime.gov.in under the 'Financial Fraud' category to receive an official complaint acknowledgement number.",
                "is_user_confirmation_required": True
            }
        ]
    },
    "DIGITAL_ARREST_EXTORTION": {
        "id": "PLAYBOOK_DIGITAL_ARREST",
        "category": "Digital Arrest Scam",
        "title": "Digital Arrest & Fake Police Coercion",
        "description": "Protective defense against impersonation of CBI, ED, Police, or Customs threatening arrest over Skype/WhatsApp.",
        "steps": [
            {
                "step_number": 1,
                "action_key": "DISCONNECT_VIDEO_CALL",
                "title": "Disconnect the Video Call Immediately",
                "priority": "IMMEDIATE",
                "description": "Indian Police, CBI, ED, and courts NEVER conduct legal hearings or place citizens under arrest via Skype or WhatsApp video calls. Hang up immediately.",
                "is_user_confirmation_required": True
            },
            {
                "step_number": 2,
                "action_key": "NEVER_SEND_VERIFICATION_DEPOSIT",
                "title": "Refuse Any 'Security Deposit' or 'RBI Clearance' Transfer",
                "priority": "IMMEDIATE",
                "description": "Government agencies do not demand asset transfers or deposits to personal/current accounts to verify funds.",
                "is_user_confirmation_required": True
            },
            {
                "step_number": 3,
                "action_key": "REPORT_TO_LOCAL_POLICE_AND_1930",
                "title": "Dial 1930 and Visit the Nearest Police Station",
                "priority": "SHORT_TERM",
                "description": "Contact India's cybercrime helpline 1930 and inform your local police station if scammers possess your Aadhaar or address details.",
                "is_user_confirmation_required": True
            },
            {
                "step_number": 4,
                "action_key": "PRESERVE_CALL_ID_SCREENSHOTS",
                "title": "Screenshot Caller ID, Badges & Letters",
                "priority": "SHORT_TERM",
                "description": "Do not delete forged arrest notices, fake Supreme Court stamps, or Skype profile names; save them as evidence for investigative tracking.",
                "is_user_confirmation_required": True
            }
        ]
    },
    "VOICE_CLONING_IMPERSONATION": {
        "id": "PLAYBOOK_VOICE_CLONING",
        "category": "Voice Cloning Fraud",
        "title": "Synthetic Audio / Executive Voice Impersonation",
        "description": "Response protocol when an urgent call or voice note sounds like a known friend, executive, or family member in distress.",
        "steps": [
            {
                "step_number": 1,
                "action_key": "HANG_UP_AND_CALL_KNOWN_NUMBER",
                "title": "Hang Up and Call Back on a Known Number",
                "priority": "IMMEDIATE",
                "description": "Do not trust caller ID alone (CLI spoofing). End the call and dial the person or family member back on their previously saved direct number.",
                "is_user_confirmation_required": True
            },
            {
                "step_number": 2,
                "action_key": "ASK_SECRET_CODEWORD",
                "title": "Establish an Offline Family / Office Codeword",
                "priority": "IMMEDIATE",
                "description": "Ask a private question only the real individual knows (e.g., childhood pet, unpublicized private event).",
                "is_user_confirmation_required": True
            },
            {
                "step_number": 3,
                "action_key": "HALT_UNVERIFIED_WIRE_TRANSFERS",
                "title": "Halt Urgent Wire Transfers",
                "priority": "IMMEDIATE",
                "description": "Never process emergency bail, accident, or corporate wire requests based solely on telephone instructions.",
                "is_user_confirmation_required": True
            }
        ]
    }
}

