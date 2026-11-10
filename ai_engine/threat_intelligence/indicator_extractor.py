"""
indicator_extractor.py — Stage 5
Extracts threat indicators (URLs, domains, IPv4, phone numbers, UPI/financial IDs)
from raw input texts, messages, or metadata.
"""
import re
from typing import Dict, List, Set
from urllib.parse import urlparse

# Regex patterns for IOC extraction
URL_PATTERN = re.compile(
    r'(?:https?:\/\/|www\.)[^\s<>"\'{}|\\^`]+',
    re.IGNORECASE
)
IPV4_PATTERN = re.compile(
    r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b'
)
DOMAIN_PATTERN = re.compile(
    r'\b(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}\b'
)
UPI_PATTERN = re.compile(
    r'\b[a-zA-Z0-9.\-_]{2,256}@[a-zA-Z]{2,64}\b'
)
PHONE_IN_PATTERN = re.compile(
    r'(?:\+91[\-\s]?)?[6-9]\d{9}\b'
)


def extract_indicators(text: str) -> Dict[str, List[str]]:
    """
    Extracts all potential IOCs from a message or text string.
    Returns:
        {
            "urls": [...],
            "domains": [...],
            "ips": [...],
            "upi_ids": [...],
            "phones": [...]
        }
    """
    if not text:
        return {"urls": [], "domains": [], "ips": [], "upi_ids": [], "phones": []}

    # 1. Extract URLs
    raw_urls = URL_PATTERN.findall(text)
    urls: List[str] = []
    domains_set: Set[str] = set()

    for u in raw_urls:
        cleaned_url = u.rstrip(".,;!?:)")
        if not cleaned_url.startswith(("http://", "https://")):
            cleaned_url = "https://" + cleaned_url
        urls.append(cleaned_url)
        try:
            parsed = urlparse(cleaned_url)
            if parsed.hostname:
                domains_set.add(parsed.hostname.lower())
        except Exception:
            pass

    # 2. Extract standalone IPs
    ips = [ip for ip in IPV4_PATTERN.findall(text) if not ip.startswith(("0.", "127.", "255."))]

    # 3. Extract standalone domains if not already extracted from URLs
    for d in DOMAIN_PATTERN.findall(text):
        d_lower = d.lower()
        if not any(d_lower in u for u in urls) and not d_lower.endswith((".exe", ".png", ".jpg", ".zip", ".pdf")):
            domains_set.add(d_lower)

    # 4. Financial & Telephony indicators
    upi_ids = [upi for upi in UPI_PATTERN.findall(text) if not upi.endswith((".com", ".org", ".net"))]
    phones = PHONE_IN_PATTERN.findall(text)

    return {
        "urls": list(dict.fromkeys(urls)),
        "domains": list(domains_set),
        "ips": list(dict.fromkeys(ips)),
        "upi_ids": list(dict.fromkeys(upi_ids)),
        "phones": list(dict.fromkeys(phones))
    }

