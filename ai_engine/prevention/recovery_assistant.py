"""
recovery_assistant.py — Stage 6
Rule-based Security Guidance Assistant providing evidence-grounded
cybersecurity advice and recovery instructions without paid LLM dependencies.
"""
from typing import Dict, Any, List
import re
from ai_engine.prevention.protection_rules import OFFICIAL_CONTACTS


class RecoveryAssistant:
    """
    Intelligent cybersecurity guidance assistant.
    Provides verifiable, factual advice regarding financial recovery,
    phishing containment, and official Indian reporting procedures.
    """

    @staticmethod
    def answer_query(query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Answers user queries based on incident playbooks and verified security doctrine.
        """
        q = query.lower().strip()
        category = "GENERAL_GUIDANCE"
        answer = ""
        action_steps: List[str] = []
        official_resources: List[Dict[str, str]] = []

        # 1. OTP / Password Shared
        if any(w in q for w in ["shared my otp", "shared otp", "gave otp", "sent otp", "entered password", "shared password", "otp"]):
            category = "ACCOUNT_COMPROMISE"
            answer = (
                "If you shared an OTP or entered your password on a suspicious site, act immediately. "
                "An attacker likely has unauthorized access or is executing a transaction right now."
            )
            action_steps = [
                "Immediately open the official banking or service website and change your account password.",
                "If an OTP for a transaction was shared, call your bank's 24/7 helpline immediately to block cards and net-banking.",
                "Review recent active sessions and click 'Log out of all other devices'.",
                "Enable an Authenticator App (TOTP) or Security Key instead of SMS for 2-factor authentication."
            ]
            official_resources = [
                {"name": "National Cyber Crime Reporting Helpline", "contact": OFFICIAL_CONTACTS["INDIA_CYBER_HELPLINE"]},
                {"name": "Cyber Crime Portal", "url": OFFICIAL_CONTACTS["INDIA_CYBERCRIME_PORTAL"]}
            ]

        # 2. Transferred Money / Financial Fraud
        elif any(w in q for w in ["transferred money", "sent money", "scammed money", "upi fraud", "paid scammer", "lost money"]):
            category = "FINANCIAL_FRAUD_RECOVERY"
            answer = (
                "You are within the critical 'Golden Hour'. In India, prompt reporting can freeze the money "
                "before the criminal withdraws it from beneficiary bank accounts or ATMs."
            )
            action_steps = [
                "Call 1930 immediately (National Cyber Crime Reporting Helpline) to file an emergency financial fraud complaint.",
                "Call your bank's fraud reporting department to request a freeze on your account and register a transaction dispute.",
                "Preserve the 12-digit UPI UTR number or IMPS reference number from your SMS/bank statement.",
                "Lodge a formal complaint online at cybercrime.gov.in."
            ]
            official_resources = [
                {"name": "Emergency Financial Fraud Helpline", "contact": "1930"},
                {"name": "National Cyber Crime Reporting Portal", "url": "https://cybercrime.gov.in"},
                {"name": "RBI Sachet Fraud Portal", "url": "https://sachet.rbi.org.in"}
            ]

        # 3. Digital Arrest / Fake Police
        elif any(w in q for w in ["digital arrest", "cbi call", "police call", "customs call", "fedex parcel", "arrest warrant", "skype call"]):
            category = "DIGITAL_ARREST_EXTORTION"
            answer = (
                "There is NO legal concept of 'Digital Arrest' under Indian Law. "
                "Neither the CBI, ED, State Police, nor Supreme Court Judges issue arrest orders or conduct hearings over WhatsApp/Skype video calls."
            )
            action_steps = [
                "Hang up the video call immediately. Do not be intimidated by forged uniforms or artificial police station backdrops.",
                "Do NOT transfer any money for 'RBI verification' or 'security clearance'.",
                "Call 1930 and inform your local police station if they threaten physical arrest.",
                "Report the caller's WhatsApp/phone number on the Department of Telecommunications Chakshu portal."
            ]
            official_resources = [
                {"name": "DoT Sanchar Saathi (Chakshu)", "url": OFFICIAL_CONTACTS["CHAKSHU_SUSPICIOUS_COMM"]},
                {"name": "Cybercrime Helpline", "contact": "1930"}
            ]

        # 4. Clicked Link / Phishing
        elif any(w in q for w in ["clicked link", "clicked a link", "opened link", "suspicious website"]):
            category = "PHISHING_EXPOSURE"
            answer = (
                "Clicking a link can expose your IP address and attempt to lure you into downloading malware or entering credentials."
            )
            action_steps = [
                "Close the browser tab immediately.",
                "Check your browser downloads folder: if any file (e.g. .apk, .exe, .zip) downloaded automatically, DO NOT OPEN IT and delete it immediately.",
                "Clear browser cookies and cached data for that domain.",
                "If you entered any credentials, immediately change your password on the official website."
            ]
            official_resources = [
                {"name": "CERT-In Incident Reporting", "url": OFFICIAL_CONTACTS["CERT_IN_INCIDENT_REPORT"]}
            ]

        # 5. Voice Cloning
        elif any(w in q for w in ["voice cloned", "fake voice", "sounded like", "deepfake call", "ai voice"]):
            category = "VOICE_CLONING_RESPONSE"
            answer = (
                "Generative AI voice cloning uses short speech snippets to mimic voice timbre and pitch. "
                "Attackers use this to pose as relatives in distress or senior executives demanding immediate funds."
            )
            action_steps = [
                "Hang up immediately and call the individual back on their pre-saved personal number.",
                "Ask a private question or secret password that only the real individual would know.",
                "Never send money or purchase gift cards based solely on telephonic instructions."
            ]
            official_resources = [
                {"name": "National Cyber Crime Helpline", "contact": "1930"}
            ]

        # 6. General / Fallback
        else:
            category = "GENERAL_CYBER_ASSISTANCE"
            answer = (
                "Cyber Raksha AI recommends adhering to core cybersecurity principles: "
                "never disclose OTPs or banking credentials, verify urgent requests out-of-band, and check all links carefully."
            )
            action_steps = [
                "Use the Cyber Raksha Unified Threat Analyzer to inspect suspicious links, messages, or voice recordings.",
                "If you suspect fraud, report the incident immediately to national helpline 1930 or cybercrime.gov.in."
            ]
            official_resources = [
                {"name": "National Cyber Crime Helpline", "contact": "1930"},
                {"name": "National Cyber Crime Portal", "url": "https://cybercrime.gov.in"}
            ]

        return {
            "query": query,
            "category": category,
            "guidance_summary": answer,
            "action_steps": action_steps,
            "official_resources": official_resources,
            "disclaimer": "This guidance is provided for defense and advisory purposes. In cases of financial theft or extortion, always contact local law enforcement and national helpline 1930 immediately."
        }
