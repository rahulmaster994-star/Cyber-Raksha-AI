"""
Cyber Raksha AI - AI Engine Safe Logging
Ensures sensitive URL components (e.g., credentials, session tokens) are sanitized.
"""
import logging
import re
import sys
from urllib.parse import urlparse, urlunparse

# Configure logger
logger = logging.getLogger("CyberRaksha_AIEngine")
if not logger.handlers:
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [AI_ENGINE] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)


def sanitize_url_for_logging(url: str) -> str:
    """
    Strips credentials, basic auth, and sensitive query tokens before logging.
    """
    try:
        parsed = urlparse(url)
        # Strip user:password if present
        netloc = parsed.netloc
        if "@" in netloc:
            parts = netloc.split("@")
            netloc = f"***:***@{parts[-1]}"

        # Mask sensitive query parameters
        query = parsed.query
        if query:
            # Mask potential sensitive keys
            sensitive_patterns = r'(token|key|password|pass|auth|secret|session|code)=[^&]*'
            query = re.sub(sensitive_patterns, r'\1=***', query, flags=re.IGNORECASE)

        sanitized = urlunparse((
            parsed.scheme,
            netloc,
            parsed.path,
            parsed.params,
            query,
            parsed.fragment
        ))
        return sanitized
    except Exception:
        return "https://[sanitized-url-format]"
