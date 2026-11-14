"""
Cyber Raksha AI - Mobile OTP Verification Service
Supports secure 6-digit cryptographic OTP generation, expiry, rate limiting, and verification.
Integrates Fast2SMS and Twilio telecom gateways with truthful delivery status reporting.
"""
import re
import logging
from datetime import datetime, timezone, timedelta
from typing import Tuple, Optional, Dict, Any
import httpx
from sqlalchemy.orm import Session
from app.models.user import User
from app.core.config import settings
from app.core.auth_utils import generate_otp

logger = logging.getLogger("cyber_raksha.otp")


def normalize_indian_mobile(mobile: str) -> Optional[str]:
    """
    Normalizes Indian mobile numbers to standard E.164 format (+91XXXXXXXXXX).
    Rejects non-Indian or invalid 10-digit formats.
    """
    clean = re.sub(r"[\s\-\(\)]", "", mobile.strip())
    if clean.startswith("+91"):
        clean = clean[3:]
    elif clean.startswith("91") and len(clean) == 12:
        clean = clean[2:]
    elif clean.startswith("0") and len(clean) == 11:
        clean = clean[1:]

    # Valid Indian mobile starts with 6, 7, 8, or 9 and has 10 digits
    if re.match(r"^[6-9]\d{9}$", clean):
        return f"+91{clean}"
    return None


def mask_mobile_number(mobile: str) -> str:
    """Masks mobile number for privacy (e.g., +91 ******4567)."""
    if not mobile or len(mobile) < 6:
        return "****"
    return f"{mobile[:3]} ******{mobile[-4:]}"


class OtpService:
    def __init__(self):
        self.mock_sms_gateway_log = []

    def _dispatch_telecom_sms(self, normalized_mobile: str, otp: str) -> Tuple[bool, str, str]:
        """
        Attempts real over-the-air telecom SMS dispatch via configured SMS providers.
        Returns (is_dispatched, channel_status, status_detail).
        """
        # 1. Fast2SMS Integration (Standard Indian SMS Gateway)
        if settings.FAST2SMS_API_KEY and settings.FAST2SMS_API_KEY.strip():
            ten_digit = normalized_mobile.replace("+91", "")
            try:
                headers = {
                    "authorization": settings.FAST2SMS_API_KEY.strip(),
                    "Content-Type": "application/json"
                }
                payload = {
                    "variables_values": otp,
                    "route": "otp",
                    "numbers": ten_digit
                }
                with httpx.Client(timeout=8.0) as client:
                    resp = client.post("https://www.fast2sms.com/dev/bulkV2", json=payload, headers=headers)
                    if resp.status_code == 200:
                        logger.info(f"Fast2SMS dispatched OTP successfully to {mask_mobile_number(normalized_mobile)}")
                        return True, "FAST2SMS_DELIVERED", "SMS dispatched over telecom network via Fast2SMS gateway."
                    else:
                        logger.warning(f"Fast2SMS API returned status {resp.status_code}: {resp.text}")
                        return False, "FAST2SMS_FAILED", f"Fast2SMS gateway returned error: {resp.status_code}"
            except Exception as e:
                logger.error(f"Fast2SMS dispatch error: {e}")
                return False, "FAST2SMS_ERROR", str(e)

        # 2. Twilio Integration (Global Gateway)
        if settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN and settings.TWILIO_FROM_NUMBER:
            try:
                auth = (settings.TWILIO_ACCOUNT_SID.strip(), settings.TWILIO_AUTH_TOKEN.strip())
                data = {
                    "To": normalized_mobile,
                    "From": settings.TWILIO_FROM_NUMBER.strip(),
                    "Body": f"Cyber Raksha AI verification code: {otp}. Valid for 10 minutes. Do not share with anyone."
                }
                url = f"https://api.twilio.com/2010-04-01/Accounts/{settings.TWILIO_ACCOUNT_SID.strip()}/Messages.json"
                with httpx.Client(timeout=8.0) as client:
                    resp = client.post(url, data=data, auth=auth)
                    if resp.status_code in (200, 201):
                        logger.info(f"Twilio dispatched OTP successfully to {mask_mobile_number(normalized_mobile)}")
                        return True, "TWILIO_DELIVERED", "SMS dispatched over telecom network via Twilio gateway."
                    else:
                        logger.warning(f"Twilio API returned status {resp.status_code}: {resp.text}")
                        return False, "TWILIO_FAILED", f"Twilio gateway returned error: {resp.status_code}"
            except Exception as e:
                logger.error(f"Twilio dispatch error: {e}")
                return False, "TWILIO_ERROR", str(e)

        # 3. No Gateway Configured - Truthful audit reporting
        logger.info(f"[SMS GATEWAY AUDIT] Physical SMS delivery awaiting telecom credentials (FAST2SMS_API_KEY or TWILIO_ACCOUNT_SID). Target: {mask_mobile_number(normalized_mobile)}")
        return False, "AWAITING_TELECOM_GATEWAY_CONFIG", "Telecom SMS Gateway API credentials not configured in server environment. OTP generated and stored securely in trusted backend database session."

    def request_otp(self, db: Session, user: User, mobile_number: str) -> Dict[str, Any]:
        """
        Generates and stores OTP for user with 10-minute expiry and attempt counter.
        Returns dict with status, masked mobile, and delivery channel details.
        """
        normalized = normalize_indian_mobile(mobile_number)
        if not normalized:
            return {
                "success": False,
                "message": "Invalid mobile number. Must be a valid 10-digit Indian mobile number (+91).",
                "masked_mobile": None,
                "delivery_channel": "NONE"
            }

        # Check if already used by another verified user
        existing = db.query(User).filter(
            User.mobile_number == normalized,
            User.is_mobile_verified == True,
            User.id != user.id
        ).first()
        if existing:
            return {
                "success": False,
                "message": "This mobile number is already registered and verified with another account.",
                "masked_mobile": None,
                "delivery_channel": "NONE"
            }

        now = datetime.now(timezone.utc)
        otp = generate_otp(6)
        expires_at = now + timedelta(minutes=settings.OTP_EXPIRY_MINUTES)

        user.mobile_number = normalized
        user.mobile_otp = otp
        user.mobile_otp_expires_at = expires_at
        user.mobile_otp_attempts = 0
        db.commit()

        # Attempt telecom dispatch
        is_sent, channel, channel_detail = self._dispatch_telecom_sms(normalized, otp)

        self.mock_sms_gateway_log.append({
            "mobile": normalized,
            "channel": channel,
            "timestamp": now.isoformat(),
            "expires_at": expires_at.isoformat()
        })

        return {
            "success": True,
            "message": "Verification OTP has been generated by the backend server.",
            "masked_mobile": mask_mobile_number(normalized),
            "telecom_delivered": is_sent,
            "delivery_channel": channel,
            "delivery_detail": channel_detail
        }

    def verify_otp(self, db: Session, user: User, entered_otp: str) -> Tuple[bool, str]:
        """
        Verifies entered OTP against stored hash/code.
        Enforces maximum attempt threshold and expiry.
        """
        if not user.mobile_otp or not user.mobile_otp_expires_at:
            return False, "No active OTP verification request found. Please request a new OTP."

        now = datetime.now(timezone.utc)
        # Check attempts
        if user.mobile_otp_attempts >= settings.OTP_MAX_ATTEMPTS:
            user.mobile_otp = None
            user.mobile_otp_expires_at = None
            db.commit()
            return False, "Maximum verification attempts exceeded. Please request a new OTP."

        # Check expiry
        expires_at = user.mobile_otp_expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)

        if now > expires_at:
            user.mobile_otp = None
            user.mobile_otp_expires_at = None
            db.commit()
            return False, "The OTP has expired. Please request a fresh OTP."

        # Check code
        if user.mobile_otp.strip() != entered_otp.strip():
            user.mobile_otp_attempts += 1
            remaining = settings.OTP_MAX_ATTEMPTS - user.mobile_otp_attempts
            db.commit()
            return False, f"Incorrect OTP. {remaining} attempt(s) remaining."

        # Success: mark verified
        user.is_mobile_verified = True
        user.mobile_otp = None
        user.mobile_otp_expires_at = None
        user.mobile_otp_attempts = 0
        db.commit()
        return True, "Mobile number successfully verified."


otp_service = OtpService()
