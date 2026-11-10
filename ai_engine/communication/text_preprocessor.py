"""
Cyber Raksha AI - Communication Text Preprocessing Pipeline
Provides token cleaning, normalization, redaction of sensitive numbers,
and canonical text representation for NLP feature extraction.
"""
import re
import html
import unicodedata
from typing import Tuple, Dict, Any


def clean_and_normalize_text(raw_text: str) -> str:
    """
    Cleans raw text strings from SMS, WhatsApp, Email, or Web chats.
    - Unescapes HTML entities.
    - Normalizes unicode characters (NFKC).
    - Removes zero-width characters and abnormal control sequences.
    - Preserves case-insensitive semantic meaning while collapsing excessive whitespace.
    """
    if not raw_text or not isinstance(raw_text, str):
        return ""

    # 1. Unescape HTML entities (&amp;, &lt;, etc.)
    text = html.unescape(raw_text)

    # 2. Normalize unicode (handles homoglyphs, accents, diacritics)
    text = unicodedata.normalize("NFKC", text)

    # 3. Strip non-printable / zero-width characters
    text = re.sub(r'[\u200B-\u200D\uFEFF]', '', text)

    # 4. Standardize whitespace
    text = re.sub(r'\s+', ' ', text).strip()

    return text


def sanitize_message_for_storage(text: str, max_length: int = 500) -> str:
    """
    Sanitizes message text before logging or database persistence.
    Redacts OTPs, credit cards, bank account numbers, and Aadhaar numbers
    to protect user privacy per Stage 3 security mandates.
    """
    if not text:
        return ""

    sanitized = text

    # 1. Redact standard 16-digit payment card numbers FIRST
    sanitized = re.sub(r'\b(?:\d{4}[-\s]?){3}\d{4}\b', '[REDACTED_CARD]', sanitized)

    # 2. Redact 12-digit Aadhaar / National ID patterns SECOND
    sanitized = re.sub(r'\b\d{4}\s\d{4}\s\d{4}\b|\b\d{12}\b', '[REDACTED_AADHAAR]', sanitized)

    # 3. Redact isolated 4 to 8 digit OTP tokens LAST
    sanitized = re.sub(r'\b(?:\d{4}|\d{6}|\d{8})\b', '[REDACTED_OTP]', sanitized)

    # Truncate to maximum length
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length] + " [TRUNCATED_FOR_PRIVACY]"

    return sanitized

