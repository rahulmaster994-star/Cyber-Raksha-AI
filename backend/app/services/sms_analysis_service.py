"""
Cyber Raksha AI - SMS Fraud Detection & Analysis Service
Phase B2: Intelligent SMS & Call Fraud Protection
"""
import hashlib
import hmac
import json
import os
import re
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from urllib.parse import urlparse
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.sms_analysis import SmsAnalysis
from app.models.threat_intel import ThreatIndicator
from app.models.security_event import SecurityEvent
from app.models.notification import Notification
from app.schemas.notification import NotificationCreate
from app.services.notification_service import NotificationService


class SmsAnalysisService:
    # URL extraction regex
    URL_REGEX = re.compile(
        r"(https?://[^\s/$.?#].[^\s]*|"
        r"(?:www\.)[^\s/$.?#].[^\s]*|"
        r"(?:bit\.ly|tinyurl\.com|t\.co|is\.gd|cutt\.ly|rb\.gy|wa\.me|t\.me)/[a-zA-Z0-9_\-]+|"
        r"[a-zA-Z0-9\-]+(?:\.[a-zA-Z0-9\-]+)*\.(?:com|in|org|net|xyz|top|site|online|club|live|link|vip|app|shop)(?:/[^\s]*)?)",
        re.IGNORECASE
    )

    SUSPICIOUS_SHORTENERS = {
        "bit.ly", "tinyurl.com", "t.co", "is.gd", "cutt.ly", "rb.gy", "wa.me", "t.me"
    }

    # Fraud pattern definitions
    PATTERNS = {
        "GOV_IMPERSONATION": [
            r"\bdigital\s+arrest\b",
            r"\bcbi\s+(?:notice|order|department|officer)\b",
            r"\bpolice\s+(?:warrant|arrest|summons|fir)\b",
            r"\bnarcotics\s+(?:control|bureau|drugs|parcel)\b",
            r"\bcustoms\s+(?:seizure|confiscation|held|parcel)\b",
            r"\bcyber\s+crime\s+(?:branch|police|department)\b",
            r"\bcourt\s+summons\b",
            r"\bed\s+(?:raid|notice|inquiry)\b"
        ],
        "OTP_FRAUD": [
            r"\bshare\s+(?:your\s+)?otp\b",
            r"\botp\s+(?:for|to)\s+(?:verification|receive|refund|claim)\b",
            r"\btell\s+(?:me\s+)?the\s+(?:otp|6\s*digit\s*code|pin)\b",
            r"\bsend\s+(?:back\s+)?otp\b",
            r"\bforward\s+(?:this\s+)?(?:otp|sms)\b",
            r"\benter\s+otp\s+to\s+receive\b"
        ],
        "UPI_FRAUD": [
            r"\benter\s+(?:your\s+)?upi\s*pin\s+to\s+receive\b",
            r"\bcollect\s+request\s+of\s+rs\b",
            r"\b(?:paytm|phonepe|gpay)\s+cashback\s+(?:of|won|received)\b",
            r"\bscan\s+(?:this\s+)?qr\s*(?:code)?\s+to\s+receive\b",
            r"\bapprove\s+(?:the\s+)?request\s+to\s+get\b",
            r"\brefund\s+(?:of\s+rs\.?|credited|approved)\b"
        ],
        "BANKING_FRAUD": [
            r"\b(?:account|debit\s*card|credit\s*card|atm)\s+(?:is|has\s+been|was)?\s*(?:blocked|suspended|deactivated|frozen)\b",
            r"\b(?:update|verify|link)\s+(?:your\s+)?(?:pan|aadhaar|kyc)\b",
            r"\bkyc\s+(?:is\s+)?(?:pending|expired|suspended|required)\b",
            r"\bunauthorized\s+(?:transaction|login|debit)\b",
            r"\bnet\s*banking\s+(?:access\s+)?(?:suspended|blocked)\b",
            r"\b(?:sbi|hdfc|icici|axis|pnb|bob|kotak)\s*(?:bank)?\s*(?:account|yono|netbanking)?\s*(?:is|has\s+been)?\s*(?:blocked|alert|kyc)\b"
        ],
        "DELIVERY_SCAM": [
            r"\b(?:parcel|package|courier|shipment)\s+(?:is\s+)?(?:on\s+hold|held|undelivered|delayed)\b",
            r"\bupdate\s+(?:delivery\s+)?address\s+(?:within|now|immediately)\b",
            r"\bpay\s+(?:pending\s+)?delivery\s+(?:fee|charges|cost)\b",
            r"\b(?:indiapost|delhivery|bluedart|speedpost)\s+(?:delivery|parcel|tracking)\b"
        ],
        "LOTTERY_SCAM": [
            r"\b(?:won|winner|claim)\s+(?:a\s+)?(?:lottery|jackpot|crorepati|prize|reward|car|iphone)\b",
            r"\bguaranteed\s+(?:returns|daily\s+profit|profit|income|bonus)\b",
            r"\bpart\s*time\s+job\s+(?:daily|earn\s+rs)\b",
            r"\btelegram\s+(?:task|group|channel|manager|rating|subscribe)\b",
            r"\bcrypto\s+(?:investment|doubler|bonus)\b",
            r"\b(?:kbc|lucky\s*draw)\b"
        ]
    }

    URGENCY_KEYWORDS = [
        r"\bimmediately\b", r"\bwithin\s+\d+\s*(?:hours|hrs|minutes|mins)\b",
        r"\btoday\b", r"\burgent\b", r"\bact\s+now\b", r"\blast\s+warning\b",
        r"\bpenalty\b", r"\blegal\s+action\b", r"\bfailure\s+to\b"
    ]

    CREDENTIAL_KEYWORDS = [
        r"\bpin\b", r"\botp\b", r"\bcvv\b", r"\bpassword\b",
        r"\bnetbanking\b", r"\bcard\s+number\b"
    ]

    def __init__(self):
        self.notification_service = NotificationService()

    @classmethod
    def extract_urls(cls, text: str) -> List[str]:
        """Extracts unique URLs and domain references from raw text."""
        raw_matches = cls.URL_REGEX.findall(text)
        urls = []
        for m in raw_matches:
            clean = m.strip().rstrip(".,;:!?)'\"")
            if clean and len(clean) > 4:
                if not clean.startswith(("http://", "https://")):
                    # Normalize domain-only to https for parsing
                    normalized = f"https://{clean}"
                else:
                    normalized = clean
                if normalized not in urls and clean not in urls:
                    urls.append(clean)
        return urls

    # Server-side cryptographic pepper for HMAC message derivation (prevents rainbow table attacks)
    # Loaded securely from environment or application settings without hardcoding production secrets
    @classmethod
    def get_pepper_key(cls) -> bytes:
        return settings.SMS_PEPPER_KEY.encode("utf-8")

    @property
    def PEPPER_KEY(self) -> bytes:
        return settings.SMS_PEPPER_KEY.encode("utf-8")

    @classmethod
    def get_all_peppers(cls) -> List[bytes]:
        """Returns list of active and historical peppers for zero-downtime key rotation."""
        peppers = [settings.SMS_PEPPER_KEY.encode("utf-8")]
        prev = os.getenv("CYBER_RAKSHA_SMS_PREVIOUS_PEPPERS", "")
        if prev:
            for p in prev.split(","):
                p_clean = p.strip()
                if p_clean and p_clean.encode("utf-8") not in peppers:
                    peppers.append(p_clean.encode("utf-8"))
        return peppers

    @classmethod
    def _hash_message(cls, text: str) -> str:
        """
        Keyed HMAC-SHA256 hash of normalized text for zero-retention privacy.
        Guarantees that dictionary, brute-force, and rainbow table attacks cannot invert
        short or formulaic SMS messages (e.g. 6-digit OTPs).
        """
        normalized = " ".join(text.strip().lower().split())
        return hmac.new(cls.get_pepper_key(), normalized.encode("utf-8"), hashlib.sha256).hexdigest()

    @classmethod
    def verify_message_hash(cls, text: str, expected_hash: str) -> bool:
        """
        Verifies a normalized message against current and historical peppers.
        Supports seamless secret rotation without breaking historical audit matches.
        """
        normalized = " ".join(text.strip().lower().split())
        for pepper in cls.get_all_peppers():
            computed = hmac.new(pepper, normalized.encode("utf-8"), hashlib.sha256).hexdigest()
            if hmac.compare_digest(computed, expected_hash):
                return True
        return False

    def analyze_sms(
        self,
        db: Session,
        device_id: str,
        message_text: str,
        sender: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Runs comprehensive multi-vector analysis on SMS message:
        1. Privacy normalization & hashing
        2. URL extraction & threat intelligence indicator lookup
        3. Fraud category pattern matching
        4. Urgency & credential demand weighting
        5. Sender header impersonation detection
        6. Risk score & recommendation synthesis
        7. Audit persistence & real-time notification generation
        """
        now = datetime.now(timezone.utc)
        msg_hash = self._hash_message(message_text)
        extracted_urls = self.extract_urls(message_text)

        detection_reasons: List[str] = []
        url_threats: List[Dict[str, Any]] = []
        risk_score = 0.0

        # 1. URL Threat Intelligence Cross-Reference
        known_malicious_url_found = False
        for raw_url in extracted_urls:
            target_str = raw_url
            if not target_str.startswith(("http://", "https://")):
                target_str = f"https://{raw_url}"

            parsed = urlparse(target_str)
            domain = parsed.hostname or raw_url

            # Check ThreatIndicator table
            match = (
                db.query(ThreatIndicator)
                .filter(
                    ThreatIndicator.is_active == True,
                    (ThreatIndicator.indicator_value == raw_url) |
                    (ThreatIndicator.indicator_value == target_str) |
                    (ThreatIndicator.indicator_value == domain)
                )
                .first()
            )

            if match:
                known_malicious_url_found = True
                url_threats.append({
                    "url": raw_url,
                    "is_malicious": True,
                    "threat_type": match.threat_type,
                    "source": match.source_name
                })
                detection_reasons.append(
                    f"Message contains verified malicious link '{domain}' indexed in {match.source_name} as {match.threat_type}."
                )
            else:
                is_shortener = any(short in domain.lower() for short in self.SUSPICIOUS_SHORTENERS)
                if is_shortener:
                    detection_reasons.append(
                        f"Message uses URL shortener '{domain}' to conceal destination domain."
                    )
                    risk_score += 20.0

                # Phase B4: Intelligent URL Feature & Brand Impersonation Correlation
                try:
                    from ai_engine.core.brand_impersonation import check_brand_impersonation
                    brand_info = check_brand_impersonation(domain)
                    if brand_info:
                        detection_reasons.append(brand_info["description"])
                        risk_score += brand_info["risk_contribution"]
                        url_threats.append({
                            "url": raw_url,
                            "is_malicious": False,
                            "threat_type": "BRAND_IMPERSONATION",
                            "source": "BRAND_DETECTOR",
                            "brand": brand_info["brand_name"]
                        })
                except Exception:
                    pass

                try:
                    from ai_engine.inference.phishing_detector import detect_phishing
                    ml_res = detect_phishing(raw_url)
                    if ml_res.success and ml_res.classification in ["PHISHING", "SUSPICIOUS"]:
                        detection_reasons.append(
                            f"Extracted link '{raw_url}' classified as {ml_res.classification} by local ML model ({ml_res.model_version})."
                        )
                        risk_score += 30.0
                        url_threats.append({
                            "url": raw_url,
                            "is_malicious": False,
                            "threat_type": "ML_PHISHING_SUSPECT",
                            "source": "LOCAL_ML"
                        })
                except Exception:
                    pass

                url_threats.append({
                    "url": raw_url,
                    "is_malicious": False,
                    "threat_type": "SUSPICIOUS_SHORTENER" if is_shortener else "UNVERIFIED_LINK",
                    "source": "HEURISTIC"
                })

        if known_malicious_url_found:
            risk_score += 65.0
        elif extracted_urls:
            # Base risk for having an unverified link in message
            risk_score += 15.0

        # 2. Fraud Category Evaluation
        matched_categories: Dict[str, int] = {}
        text_lower = message_text.lower()

        for category, patterns in self.PATTERNS.items():
            cat_matches = 0
            for pat in patterns:
                if re.search(pat, text_lower):
                    cat_matches += 1
            if cat_matches > 0:
                matched_categories[category] = cat_matches

        # Phase B4 False-Positive Safeguard:
        # Distinguish legitimate outbound OTP notices ("OTP: 123456 for your transaction. Do not share.")
        # and standard receipts from fraudulent phishing attempts.
        is_legitimate_otp_receipt = (
            ("do not share" in text_lower or "never share" in text_lower) and
            not any(req in text_lower for req in ["share your otp", "send otp", "tell me the otp", "send back otp", "enter otp to receive"]) and
            not extracted_urls
        )
        if is_legitimate_otp_receipt:
            if "OTP_FRAUD" in matched_categories:
                del matched_categories["OTP_FRAUD"]
            detection_reasons.append(
                "Standard outbound security notice detected ('do not share'); confirmed legitimate receipt."
            )
            risk_score = max(0.0, risk_score - 20.0)

        # Determine primary fraud category
        primary_category = "BENIGN"
        if matched_categories:
            primary_category = max(matched_categories, key=matched_categories.get)
            match_count = matched_categories[primary_category]

            if primary_category == "GOV_IMPERSONATION":
                risk_score += 55.0 + (match_count * 10.0)
                detection_reasons.append(
                    "Detected high-severity government/police intimidation language typical of 'Digital Arrest' extortion schemes."
                )
            elif primary_category == "OTP_FRAUD":
                risk_score += 50.0 + (match_count * 10.0)
                detection_reasons.append(
                    "Detected explicit attempt to harvest One-Time Passwords (OTP) or authentication codes."
                )
            elif primary_category == "UPI_FRAUD":
                risk_score += 45.0 + (match_count * 8.0)
                detection_reasons.append(
                    "Detected fraudulent payment collection or deceptive UPI cashback/refund pretext."
                )
            elif primary_category == "BANKING_FRAUD":
                risk_score += 45.0 + (match_count * 8.0)
                detection_reasons.append(
                    "Detected fake account suspension, KYC update urgency, or banking impersonation."
                )
            elif primary_category == "DELIVERY_SCAM":
                risk_score += 40.0 + (match_count * 8.0)
                detection_reasons.append(
                    "Detected package hold/customs fee pretext commonly used for credential and payment theft."
                )
            elif primary_category == "LOTTERY_SCAM":
                risk_score += 50.0 + (match_count * 10.0)
                detection_reasons.append(
                    "Detected unsolicited lottery, cryptocurrency, or task-based investment scheme."
                )

        # 3. Urgency & High-Pressure Indicators
        urgency_matches = [p for p in self.URGENCY_KEYWORDS if re.search(p, text_lower)]
        if urgency_matches:
            risk_score += min(30.0, len(urgency_matches) * 12.0)
            detection_reasons.append(
                "Employs manufactured urgency and coercive deadlines to bypass rational evaluation."
            )

        # 4. Credential Harvest Demands
        cred_matches = [p for p in self.CREDENTIAL_KEYWORDS if re.search(p, text_lower)]
        if cred_matches and primary_category != "OTP_FRAUD" and not is_legitimate_otp_receipt:
            risk_score += 30.0
            detection_reasons.append(
                "Requests sensitive credentials (PIN, CVV, Password) via unauthenticated channel."
            )

        # 5. Sender Header Impersonation
        if sender:
            s_clean = sender.strip()
            # If claiming banking/gov from 10-digit standard personal mobile number
            digits = re.sub(r"\D", "", s_clean)
            if (len(digits) == 10 or (len(digits) == 12 and digits.startswith("91"))) and primary_category in {
                "BANKING_FRAUD", "GOV_IMPERSONATION", "DELIVERY_SCAM"
            }:
                risk_score += 20.0
                detection_reasons.append(
                    f"Official institution notification simulated from personal mobile number ({sender})."
                )

        # Normalize score
        final_score = min(100.0, max(0.0, round(risk_score, 1)))

        # Assign risk level
        if final_score >= 80.0:
            risk_level = "CRITICAL"
        elif final_score >= 60.0:
            risk_level = "HIGH"
        elif final_score >= 35.0:
            risk_level = "MEDIUM"
        elif final_score >= 15.0:
            risk_level = "LOW"
        else:
            risk_level = "SAFE"
            if not detection_reasons:
                detection_reasons.append("No recognized fraud signatures, coercive patterns, or malicious URLs detected.")

        recommended_action = self._determine_recommendation(risk_level, primary_category)

        # 6. Database Persistence (Hash only, no plain text)
        analysis_record = SmsAnalysis(
            device_id=device_id,
            message_hash=msg_hash,
            risk_score=final_score,
            risk_level=risk_level,
            fraud_category=primary_category,
            detection_reasons=json.dumps(detection_reasons),
            urls_found=json.dumps(extracted_urls) if extracted_urls else None,
            analyzed_at=now,
            is_false_positive=False
        )
        db.add(analysis_record)
        db.commit()
        db.refresh(analysis_record)

        # 7. Escalation & Real-Time Alerting for HIGH & CRITICAL
        if risk_level in {"HIGH", "CRITICAL"}:
            notif_payload = NotificationCreate(
                title=f"Mobile Fraud Alert: {primary_category.replace('_', ' ').title()}",
                message=f"Threat detected on mobile device {device_id[:8]}: {detection_reasons[0]}",
                severity=risk_level,
                category="SECURITY_ALERT",
                target_domain=extracted_urls[0] if extracted_urls else sender or "SMS_INTERCEPTOR",
                recommended_action=recommended_action,
                source_component="SMS_PROTECTION_ENGINE",
                metadata_json={
                    "device_id": device_id,
                    "risk_score": final_score,
                    "fraud_category": primary_category,
                    "message_hash": msg_hash
                }
            )
            try:
                self.notification_service.create_notification(db, notif_payload)
            except Exception as e:
                # Non-fatal notification failure
                pass

        return {
            "message_hash": msg_hash,
            "risk_score": final_score,
            "risk_level": risk_level,
            "fraud_category": primary_category,
            "detection_reasons": detection_reasons,
            "extracted_urls": extracted_urls,
            "url_threats": url_threats,
            "recommended_action": recommended_action,
            "analyzed_at": now
        }

    @staticmethod
    def _determine_recommendation(risk_level: str, category: str) -> str:
        if category == "OTP_FRAUD" and risk_level in {"HIGH", "CRITICAL"}:
            return "DO NOT SHARE OTP: Sharing this code will grant attackers immediate access to your account or funds."
        if category == "GOV_IMPERSONATION" and risk_level in {"HIGH", "CRITICAL"}:
            return "CRITICAL DANGER: Law enforcement agencies never conduct 'Digital Arrest' via video or SMS. Do not comply and disconnect immediately."
        if risk_level == "CRITICAL":
            return "HIGH FRAUD ALERT: Do not open links, transfer funds, or call any phone numbers listed in this message."
        elif risk_level == "HIGH":
            return "WARNING: Suspicious message exhibiting recognized fraud patterns. Verify directly through official app or customer care."
        elif risk_level == "MEDIUM":
            return "CAUTION: Unverified message containing links or urgency. Exercise vigilance before taking action."
        elif risk_level == "LOW":
            return "Standard message. No active threat indicators detected, but stay mindful."
        return "Message appears safe. No suspicious signals identified."


sms_analysis_service = SmsAnalysisService()
