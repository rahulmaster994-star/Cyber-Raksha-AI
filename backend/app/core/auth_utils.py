"""
Cyber Raksha AI - Cryptographic Authentication & Token Utilities
Pure Python standard library implementation: HMAC, PBKDF2-SHA256, secrets.
"""
import base64
import hashlib
import hmac
import json
import secrets
import string
import time
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any
from app.core.config import settings


def hash_password(password: str) -> str:
    """
    Hashes a password using PBKDF2-HMAC-SHA256 with a 16-byte random salt and 100,000 iterations.
    Format: pbkdf2_sha256$<iterations>$<salt_hex>$<hash_hex>
    """
    salt = secrets.token_bytes(16)
    iterations = 100_000
    hash_bytes = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return f"pbkdf2_sha256${iterations}${salt.hex()}${hash_bytes.hex()}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifies a plain password against the stored PBKDF2-HMAC-SHA256 hash.
    Constant-time comparison via hmac.compare_digest.
    """
    try:
        parts = hashed_password.split("$")
        if len(parts) != 4 or parts[0] != "pbkdf2_sha256":
            return False
        iterations = int(parts[1])
        salt = bytes.fromhex(parts[2])
        expected_hash = parts[3]
        calculated_hash = hashlib.pbkdf2_hmac("sha256", plain_password.encode("utf-8"), salt, iterations).hex()
        return hmac.compare_digest(expected_hash, calculated_hash)
    except Exception:
        return False


def create_access_token(payload: Dict[str, Any], expires_minutes: int = 1440) -> str:
    """
    Creates a cryptographically signed URL-safe JWT-compatible access token using HMAC-SHA256.
    Header.Payload.Signature format.
    """
    header = {"alg": "HS256", "typ": "JWT"}
    exp = int(time.time()) + (expires_minutes * 60)
    data = dict(payload)
    data["exp"] = exp
    data["iat"] = int(time.time())

    header_b64 = base64.urlsafe_b64encode(json.dumps(header, separators=(",", ":")).encode("utf-8")).rstrip(b"=").decode("utf-8")
    payload_b64 = base64.urlsafe_b64encode(json.dumps(data, separators=(",", ":")).encode("utf-8")).rstrip(b"=").decode("utf-8")
    signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")

    key = settings.JWT_SECRET_KEY.encode("utf-8")
    sig = hmac.new(key, signing_input, hashlib.sha256).digest()
    sig_b64 = base64.urlsafe_b64encode(sig).rstrip(b"=").decode("utf-8")

    return f"{header_b64}.{payload_b64}.{sig_b64}"


def verify_access_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Verifies signature and expiration of an access token.
    Returns decoded payload if valid, None otherwise.
    """
    try:
        parts = token.strip().split(".")
        if len(parts) != 3:
            return None
        header_b64, payload_b64, sig_b64 = parts

        signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")
        key = settings.JWT_SECRET_KEY.encode("utf-8")
        expected_sig = hmac.new(key, signing_input, hashlib.sha256).digest()

        # Add padding back
        pad_len = (4 - len(sig_b64) % 4) % 4
        decoded_sig = base64.urlsafe_b64decode(sig_b64 + "=" * pad_len)

        if not hmac.compare_digest(expected_sig, decoded_sig):
            return None

        pad_payload = (4 - len(payload_b64) % 4) % 4
        payload_json = base64.urlsafe_b64decode(payload_b64 + "=" * pad_payload).decode("utf-8")
        payload = json.loads(payload_json)

        # Check expiration
        if "exp" in payload and time.time() > payload["exp"]:
            return None

        return payload
    except Exception:
        return None


def generate_otp(length: int = 6) -> str:
    """Generates a cryptographically secure numeric OTP."""
    digits = string.digits
    return "".join(secrets.choice(digits) for _ in range(length))


def generate_verification_token() -> str:
    """Generates a secure random URL-safe verification token."""
    return secrets.token_urlsafe(32)

