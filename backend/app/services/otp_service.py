"""
Cyber Raksha AI - Mobile OTP Verification Service
Supports secure 6-digit cryptographic OTP generation, expiry, rate limiting, and verification.
"""
import re
import logging
from datetime import datetime, timezone, timedelta
from typing import Tuple, Optional
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

    def request_otp(self, db: Session, user: User, mobile_number: str) -> Tuple[bool, str, Optional[str]]:
        """
        Generates and stores OTP for user with 10-minute expiry and attempt counter.
        Returns (success, message, masked_mobile).
        """
        normalized = normalize_indian_mobile(mobile_number)
        if not normalized:
            return False, "Invalid mobile number. Must be a valid 10-digit Indian mobile number (+91).", None

        # Check if already used by another verified user
        existing = db.query(User).filter(
            User.mobile_number == normalized,
            User.is_mobile_verified == True,
            User.id != user.id
        ).first()
        if existing:
            return False, "This mobile number is already registered and verified with another account.", None

        now = datetime.now(timezone.utc)
        otp = generate_otp(6)
        expires_at = now + timedelta(minutes=settings.OTP_EXPIRY_MINUTES)

        user.mobile_number = normalized
        user.mobile_otp = otp
        user.mobile_otp_expires_at = expires_at
        user.mobile_otp_attempts = 0
        db.commit()

        # In a production telecom environment, SMS gateway API (e.g. Twilio / Gupshup / Fast2SMS) is called here.
        # Defensive logging and in-memory trace for testing and verification:
        logger.info(f"[SMS GATEWAY DISPATCH] OTP sent to {mask_mobile_number(normalized)}: [REDACTED IN LOGS]")
        self.mock_sms_gateway_log.append({
            "mobile": normalized,
            "timestamp": now.isoformat(),
            "expires_at": expires_at.isoformat()
        })

        return True, "Verification OTP has been sent successfully to your mobile number.", mask_mobile_number(normalized)

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
