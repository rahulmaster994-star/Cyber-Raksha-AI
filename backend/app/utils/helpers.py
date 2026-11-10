"""
Cyber Raksha AI - Utility Functions
"""
import hashlib
import secrets
from datetime import datetime, timezone
from typing import Optional


def get_current_utc() -> datetime:
    """Returns the current timezone-aware UTC datetime."""
    return datetime.now(timezone.utc)


def hash_password_fallback(password: str) -> str:
    """
    Secure salted SHA-256 hash suitable for development and Stage 1 baseline.
    Avoids native binary dependencies if passlib/bcrypt are omitted.
    """
    salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100_000)
    return f"{salt}:{key.hex()}"


def verify_password_fallback(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain password against the stored salt:hash."""
    try:
        salt, key_hex = hashed_password.split(":")
        new_key = hashlib.pbkdf2_hmac("sha256", plain_password.encode("utf-8"), salt.encode("utf-8"), 100_000)
        return secrets.compare_digest(new_key.hex(), key_hex)
    except Exception:
        return False


# ==============================================================================
# Phase B3.1: Deterministic Threat Indicator Normalization
# ==============================================================================

import re
from urllib.parse import urlparse, parse_qsl, urlencode, urlunparse


def normalize_threat_indicator(indicator: Optional[str], indicator_type: Optional[str] = None) -> Optional[str]:
    """
    Deterministically normalizes a threat indicator (URL, domain, or phone number)
    to guarantee accurate deduplication, cross-vector correlation, and database querying.
    """
    if not indicator:
        return None

    trimmed = indicator.strip()
    if not trimmed:
        return None

    ind_type = (indicator_type or "").upper()

    # Detect phone number indicators
    if ind_type in {"PHONE", "PHONE_NUMBER", "CALLER"} or (
        not ind_type and re.match(r"^(\+?\d[\d\s\-\.\(\)]{6,}\d)$", trimmed) and not ("/" in trimmed or "." in trimmed and not trimmed.replace(".", "").isdigit())
    ):
        return normalize_phone_indicator(trimmed)

    # Detect URL / domain indicators
    if ind_type in {"URL", "DOMAIN"} or "://" in trimmed or "/" in trimmed or "." in trimmed:
        return normalize_url_indicator(trimmed)

    return trimmed


# Known signature query keys used in HMAC / signed URLs (AWS S3, Azure SAS, Google Cloud Storage, signed links)
_SIGNATURE_QUERY_KEYS = {
    "signature", "x-amz-signature", "sig", "hmac", "token_signature",
    "sp", "sv", "se", "mac", "sign", "auth_token"
}


def is_signed_url(query: str) -> bool:
    """Detects whether a URL query string contains cryptographic signature parameters."""
    if not query:
        return False
    lower_query = query.lower()
    return any(f"{key}=" in lower_query or lower_query.startswith(f"{key}=") for key in _SIGNATURE_QUERY_KEYS)


def normalize_url_indicator(url: str, preserve_signed_query: bool = True) -> str:
    """
    Normalizes URLs and domains with safe, non-destructive canonicalization:
    - Lowercases scheme and host.
    - Encodes Internationalized Domain Names (IDN) to ASCII punycode (RFC 3492).
    - Strips default ports (:80 for HTTP, :443 for HTTPS).
    - Removes client-side fragments (#...) which are browser-only and never sent to servers.
    - Strips trailing slash on root paths (/), preserving explicit resource paths (/path/).
    - Preserves repeated query parameters with multiple values.
    - Detects signed URLs (AWS S3, Azure SAS, HMAC signatures): preserves exact query order
      so cryptographic signatures and verification hashes remain valid.
    - For non-signed URLs: sorts query parameters deterministically by (key, value).
    - Handles malformed URLs gracefully without crashing.
    """
    if not url or not isinstance(url, str):
        return ""

    clean = url.strip()
    if not clean:
        return ""

    if not re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", clean):
        # Bare domain or path without scheme
        clean = "http://" + clean

    try:
        parsed = urlparse(clean)
    except Exception:
        return url.strip().lower()

    scheme = (parsed.scheme or "http").lower()
    netloc_raw = parsed.netloc.lower()

    # Split host and port
    if ":" in netloc_raw and not netloc_raw.endswith("]"):  # Guard against IPv6 [::1]
        host_part, port_part = netloc_raw.rsplit(":", 1)
    else:
        host_part, port_part = netloc_raw, None

    # Handle Internationalized Domain Names (IDN) / Punycode conversion
    try:
        # Strip brackets if IPv6
        if host_part.startswith("[") and host_part.endswith("]"):
            encoded_host = host_part
        else:
            encoded_host = host_part.encode("idna").decode("ascii")
    except Exception:
        encoded_host = host_part

    # Remove default ports
    if (scheme == "http" and port_part == "80") or (scheme == "https" and port_part == "443"):
        port_part = None

    netloc = f"{encoded_host}:{port_part}" if port_part else encoded_host

    path = parsed.path
    if path == "/":
        path = ""
    elif path.endswith("/") and len(path) > 1:
        path = path.rstrip("/")

    # Query handling: preserve signed URLs, sort non-signed URLs, keep duplicate parameters
    final_query = ""
    if parsed.query:
        if preserve_signed_query and is_signed_url(parsed.query):
            # Preserve original query order for cryptographically signed URLs
            final_query = parsed.query
        else:
            query_pairs = parse_qsl(parsed.query, keep_blank_values=True)
            # Deterministic stable sort preserving duplicate keys with their values
            query_pairs.sort(key=lambda x: (x[0], x[1]))
            final_query = urlencode(query_pairs)

    normalized = urlunparse((scheme, netloc, path, "", final_query, ""))
    return normalized


def normalize_phone_indicator(phone: str) -> str:
    """
    Normalizes phone numbers into standardized international format.
    Removes spaces, dashes, parentheses, dots.
    Standardizes standard Indian mobile prefixing (+91).
    """
    if not phone:
        return ""
    trimmed = phone.strip()
    has_plus = trimmed.startswith("+")
    digits_only = re.sub(r"\D", "", trimmed)

    if not digits_only:
        return trimmed

    # Standardize Indian 10-digit mobile
    if len(digits_only) == 10:
        return f"+91{digits_only}"
    elif len(digits_only) == 11 and digits_only.startswith("0"):
        return f"+91{digits_only[1:]}"
    elif len(digits_only) == 12 and digits_only.startswith("91"):
        return f"+{digits_only}"

    if has_plus:
        return f"+{digits_only}"
    return digits_only

