"""
Cyber Raksha AI - URL Feature Extraction Engine
Extracts 25+ structural, lexical, and behavioral characteristics without executing remote network calls.
"""
import ipaddress
import re
from typing import Dict, Any, List
from urllib.parse import urlparse, parse_qs

from ai_engine.utils.config import SUSPICIOUS_KEYWORDS, FEATURE_NAMES
from ai_engine.utils.validation import validate_url


def is_ip_address(hostname: str) -> int:
    """Detects if hostname is a raw IPv4 or IPv6 address."""
    # Strip port if present
    host = hostname.split(":")[0] if ":" in hostname else hostname
    # Strip brackets for IPv6
    host = host.strip("[]")
    try:
        ipaddress.ip_address(host)
        return 1
    except ValueError:
        return 0


def count_consecutive_run(text: str) -> int:
    """Finds the maximum length of consecutive identical characters."""
    if not text:
        return 0
    max_run = 1
    current_run = 1
    for i in range(1, len(text)):
        if text[i] == text[i - 1]:
            current_run += 1
            if current_run > max_run:
                max_run = current_run
        else:
            current_run = 1
    return max_run


def extract_url_features(url: str) -> Dict[str, Any]:
    """
    Extracts all numerical features and structural properties from a given URL.
    Does NOT connect to or load the target website.
    """
    is_valid, normalized_url, err = validate_url(url)
    if not is_valid:
        raise ValueError(f"Cannot extract features: {err}")

    parsed = urlparse(normalized_url)
    netloc = parsed.netloc.lower()
    path = parsed.path
    query = parsed.query
    hostname = netloc.split(":")[0] if ":" in netloc else netloc

    # Subdomain calculation
    parts = hostname.split(".")
    # If IPv4 or localhost, subdomains = 0
    if is_ip_address(hostname) or hostname == "localhost":
        subdomain_count = 0
        tld_length = 0
    elif len(parts) <= 2:
        subdomain_count = 0
        tld_length = len(parts[-1]) if len(parts) > 1 else 0
    else:
        # e.g., 'sub.domain.co.uk' or 'sub.domain.com'
        subdomain_count = len(parts) - 2
        tld_length = len(parts[-1])

    # Count characters
    url_len = len(normalized_url)
    domain_len = len(hostname)
    path_len = len(path)
    dot_count = normalized_url.count(".")
    hyphen_count = normalized_url.count("-")
    underscore_count = normalized_url.count("_")
    slash_count = normalized_url.count("/")
    question_mark_count = normalized_url.count("?")
    equal_count = normalized_url.count("=")
    at_symbol_count = normalized_url.count("@")
    percent_count = normalized_url.count("%")

    # Special characters outside alphanumeric, '.', '-', '/', ':', '?', '=', '&', '%'
    special_chars = set("!$*+,'();#[]~")
    special_char_count = sum(1 for c in normalized_url if c in special_chars)

    # Keywords detection in full URL (case-insensitive)
    lower_url = normalized_url.lower()
    keyword_matches = [kw for kw in SUSPICIOUS_KEYWORDS if kw in lower_url]
    suspicious_keyword_count = len(keyword_matches)

    # Suspicious Port check (standard web ports: 80, 443, 8000, 8080, empty)
    has_suspicious_port = 0
    if ":" in netloc:
        port_part = netloc.split(":")[-1]
        if port_part.isdigit():
            port_num = int(port_part)
            if port_num not in [80, 443, 8080, 8443]:
                has_suspicious_port = 1

    # Digits and letters
    digit_count = sum(1 for c in normalized_url if c.isdigit())
    letter_count = sum(1 for c in normalized_url if c.isalpha())
    digit_to_letter_ratio = round(digit_count / (letter_count + 1), 4)

    # Query params count
    query_params = parse_qs(query)
    query_param_count = len(query_params)

    # Punycode / IDN detection
    is_punycode = 1 if "xn--" in hostname else 0

    features = {
        "url_length": url_len,
        "domain_length": domain_len,
        "dot_count": dot_count,
        "hyphen_count": hyphen_count,
        "underscore_count": underscore_count,
        "slash_count": slash_count,
        "question_mark_count": question_mark_count,
        "equal_count": equal_count,
        "at_symbol_count": at_symbol_count,
        "percent_count": percent_count,
        "special_char_count": special_char_count,
        "subdomain_count": subdomain_count,
        "has_ip_address": is_ip_address(hostname),
        "is_https": 1 if parsed.scheme == "https" else 0,
        "suspicious_keyword_count": suspicious_keyword_count,
        "has_at_symbol": 1 if at_symbol_count > 0 else 0,
        "has_suspicious_port": has_suspicious_port,
        "path_length": path_len,
        "query_param_count": query_param_count,
        "digit_count": digit_count,
        "letter_count": letter_count,
        "digit_to_letter_ratio": digit_to_letter_ratio,
        "tld_length": tld_length,
        "is_punycode_or_idn": is_punycode,
        "consecutive_char_run": count_consecutive_run(normalized_url)
    }

    return features


def identify_risk_indicators(features: Dict[str, Any], url: str) -> List[str]:
    """
    Translates extracted characteristics into explainable cybersecurity risk indicators.
    """
    indicators: List[str] = []

    if features.get("has_ip_address", 0) == 1:
        indicators.append("Host is an IP address instead of a registered domain name (common in evasion).")

    if features.get("has_at_symbol", 0) == 1:
        indicators.append("Contains '@' symbol: Browsers ignore preceding characters and route to domain following '@'.")

    if features.get("subdomain_count", 0) >= 3:
        indicators.append(f"Excessive subdomain nesting ({features['subdomain_count']} subdomains) often disguises genuine destination.")

    if features.get("url_length", 0) > 85:
        indicators.append(f"Abnormally long URL ({features['url_length']} characters) commonly used to pad malicious tokens.")

    if features.get("percent_count", 0) >= 3:
        indicators.append(f"Multiple percent-encoded characters ({features['percent_count']}) indicating potential obfuscation.")

    if features.get("suspicious_keyword_count", 0) >= 2:
        indicators.append(f"Contains multiple high-risk credential keywords ({features['suspicious_keyword_count']} detected).")

    if features.get("has_suspicious_port", 0) == 1:
        indicators.append("Uses an irregular, non-standard web communications port.")

    if features.get("is_punycode_or_idn", 0) == 1:
        indicators.append("Punycode (xn--) detected: Possible internationalized homograph impersonation attack.")

    if features.get("is_https", 1) == 0:
        indicators.append("Insecure plain HTTP connection: Sensitive data transferred without transport encryption.")

    if features.get("hyphen_count", 0) >= 3:
        indicators.append(f"Elevated hyphen count ({features['hyphen_count']}) typically used in typo-squatting or brand impersonation.")

    if features.get("digit_to_letter_ratio", 0) > 0.4:
        indicators.append("High digit-to-letter ratio suggesting machine-generated or entropy-heavy domains.")

    return indicators
