"""
Cyber Raksha AI - URL Input Validation
Validates URLs against RFC specifications, size limits, and security constraints.
"""
import re
from typing import Tuple
from urllib.parse import urlparse

# Maximum allowed URL length to prevent memory abuse/DoS
MAX_URL_LENGTH = 2048
MIN_URL_LENGTH = 3

# RFC-compliant URL regex baseline
URL_REGEX = re.compile(
    r'^(?:http|https)://'  # http:// or https://
    r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
    r'localhost|'  # localhost...
    r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
    r'(?::\d+)?'  # optional port
    r'(?:/?|[/?]\S+)$', re.IGNORECASE
)


def validate_url(url: str) -> Tuple[bool, str, str]:
    """
    Validates a submitted URL string.
    Returns (is_valid, normalized_url, error_message).
    """
    if not url or not isinstance(url, str):
        return False, "", "URL cannot be empty or non-string."

    trimmed = url.strip()

    if len(trimmed) < MIN_URL_LENGTH:
        return False, "", f"URL is too short (minimum {MIN_URL_LENGTH} characters)."

    if len(trimmed) > MAX_URL_LENGTH:
        return False, "", f"URL exceeds maximum allowed length ({MAX_URL_LENGTH} characters)."

    # Prepend http:// if user passed a bare domain for analysis convenience
    normalized = trimmed
    if not (normalized.startswith("http://") or normalized.startswith("https://")):
        normalized = f"http://{normalized}"

    try:
        parsed = urlparse(normalized)
        if not parsed.netloc:
            return False, "", "Invalid URL: Missing hostname or domain component."

        # Verify domain does not contain forbidden control characters
        if any(c in parsed.netloc for c in [' ', '<', '>', '"', '\\', '{', '}', '|', '^', '`']):
            return False, "", "Invalid URL: Hostname contains illegal characters."

        # Netloc must have a valid dot for domains or be localhost or valid IP
        netloc = parsed.netloc.split(':')[0]
        if netloc != "localhost" and not re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', netloc):
            if "." not in netloc:
                return False, "", "Invalid URL: Hostname must contain a top-level domain."

        return True, normalized, ""
    except Exception as e:
        return False, "", f"URL parsing error: {str(e)}"
