"""
Stage 11 — URL Detection Red-Team Test Suite
Independent validation of the phishing detection model and security controls.
All test cases use controlled, synthetic, or publicly-documented safe fixtures.
No real external requests are made.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)
BYPASS = {"x-test-bypass-rate-limit": "true"}

# ---------------------------------------------------------------------------
# Test case definitions
# category: "phishing" | "legitimate" | "invalid" | "ssrf" | "edge"
# ---------------------------------------------------------------------------
URL_TEST_CASES = [
    # --- Legitimate ---
    {"id": "L-01", "url": "https://www.google.com/", "expected_safe": True, "category": "legitimate"},
    {"id": "L-02", "url": "https://github.com/", "expected_safe": True, "category": "legitimate"},
    {"id": "L-03", "url": "https://en.wikipedia.org/wiki/Main_Page", "expected_safe": True, "category": "legitimate"},
    {"id": "L-04", "url": "https://www.microsoft.com/en-us", "expected_safe": True, "category": "legitimate"},
    {"id": "L-05", "url": "https://stackoverflow.com/questions", "expected_safe": True, "category": "legitimate"},

    # --- Known phishing patterns (synthetic/structural) ---
    {"id": "P-01", "url": "http://paypal.com.secure-login-verify.phishtest.invalid/account/confirm", "expected_safe": False, "category": "phishing"},
    {"id": "P-02", "url": "http://198.51.100.25/bank/login.php?session=0xdeadbeef", "expected_safe": False, "category": "phishing"},
    {"id": "P-03", "url": "http://sbi-online.netbanking.update-kyc.phishtest.invalid/secure", "expected_safe": False, "category": "phishing"},
    {"id": "P-04", "url": "http://www.amazon-securityalert-verify.phishtest.invalid/signin", "expected_safe": False, "category": "phishing"},
    {"id": "P-05", "url": "http://login-hdfc.phishtest.invalid/netbanking?redirect=true&token=abc123", "expected_safe": False, "category": "phishing"},
    {"id": "P-06", "url": "http://aadhaar-kyc-update.gov.in.phishtest.invalid/ekyc/confirm", "expected_safe": False, "category": "phishing"},
    {"id": "P-07", "url": "http://bit.ly.phishtest.invalid/xyz12345", "expected_safe": False, "category": "phishing"},

    # --- Structural / suspicious (may classify as SUSPICIOUS not PHISHING) ---
    {"id": "S-01", "url": "http://xn--pypal-4ve.com.phishtest.invalid/", "expected_safe": False, "category": "suspicious"},
    {"id": "S-02", "url": "http://example.com.phishtest.invalid:8080/login?next=/dashboard", "expected_safe": False, "category": "suspicious"},
    {"id": "S-03", "url": "http://" + "a" * 150 + ".phishtest.invalid/", "expected_safe": False, "category": "suspicious"},
    {"id": "S-04", "url": "https://www.paypal.com.phishtest.invalid/account", "expected_safe": False, "category": "suspicious"},
    {"id": "S-05", "url": "http://google.com.phishtest.invalid/signin", "expected_safe": False, "category": "suspicious"},

    # --- Encoded / obfuscated ---
    {"id": "E-01", "url": "http://phishtest.invalid/redirect?url=http%3A%2F%2Fevil.phishtest.invalid", "expected_safe": False, "category": "encoded"},
    {"id": "E-02", "url": "http://user%40phishtest.invalid/account", "expected_safe": False, "category": "encoded"},

    # --- IP-based URLs ---
    {"id": "IP-01", "url": "http://203.0.113.5/login.php", "expected_safe": False, "category": "ip_url"},
    {"id": "IP-02", "url": "http://198.51.100.1/account/verify", "expected_safe": False, "category": "ip_url"},

    # --- Long URLs ---
    {"id": "LG-01", "url": "https://phishtest.invalid/?" + "param=value&" * 30, "expected_safe": False, "category": "long_url"},

    # --- Edge / boundary ---
    {"id": "EG-01", "url": "https://phishtest.invalid", "expected_safe": False, "category": "edge"},
    {"id": "EG-02", "url": "https://www.example.com/", "expected_safe": True, "category": "edge"},
]

# SSRF / dangerous URLs — must be REJECTED with 400, not analyzed
BLOCKED_URL_CASES = [
    {"id": "SSRF-01", "url": "http://127.0.0.1:8000/api/health", "reason": "loopback"},
    {"id": "SSRF-02", "url": "http://169.254.169.254/latest/meta-data/", "reason": "link-local metadata"},
    {"id": "SSRF-03", "url": "http://192.168.1.1/admin", "reason": "private network"},
    {"id": "SSRF-04", "url": "http://10.0.0.1/secret", "reason": "private class A"},
    {"id": "SSRF-05", "url": "javascript:alert(1)", "reason": "dangerous scheme"},
    {"id": "SSRF-06", "url": "file:///etc/passwd", "reason": "file scheme"},
    {"id": "SSRF-07", "url": "data:text/html,<script>alert(1)</script>", "reason": "data scheme"},
    {"id": "INV-01", "url": "", "reason": "empty URL"},
    {"id": "INV-02", "url": "   ", "reason": "whitespace only"},
]

MALFORMED_URL_CASES = [
    {"id": "INV-03", "url": "not-a-url-at-all", "reason": "no scheme or domain structure"},
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _post_url(url: str):
    return client.post(
        "/api/v1/detection/url",
        json={"url": url},
        headers=BYPASS,
    )


def _is_safe_classification(resp_json: dict) -> bool:
    cls = resp_json.get("classification", "").upper()
    lvl = resp_json.get("risk_level", "").upper()
    score = resp_json.get("risk_score", 0.0)
    return cls in ("LEGITIMATE",) and lvl in ("LOW",) and score < 40.0


# ---------------------------------------------------------------------------
# SSRF / blocked URL tests — must all return 400 or 422
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("case", BLOCKED_URL_CASES, ids=[c["id"] for c in BLOCKED_URL_CASES])
def test_blocked_urls_rejected(case):
    """All SSRF, dangerous-scheme, and empty URLs must be blocked (400/422), never analyzed."""
    resp = _post_url(case["url"])
    assert resp.status_code in (400, 422), (
        f"[{case['id']}] Expected 400/422 for '{case['reason']}', got {resp.status_code}. "
        f"Body: {resp.text[:200]}"
    )


@pytest.mark.parametrize("case", MALFORMED_URL_CASES, ids=[c["id"] for c in MALFORMED_URL_CASES])
def test_malformed_urls_handled_safely(case):
    """Malformed URLs without scheme return 200 with classification=INVALID."""
    resp = _post_url(case["url"])
    assert resp.status_code == 200
    data = resp.json()
    assert data["classification"] == "INVALID"
    assert data["success"] is False


# ---------------------------------------------------------------------------
# Detection quality tests
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("case", URL_TEST_CASES, ids=[c["id"] for c in URL_TEST_CASES])
def test_url_analysis_returns_valid_response(case):
    """Every analysis URL must return 200 with a well-formed JSON response."""
    resp = _post_url(case["url"])
    assert resp.status_code == 200, (
        f"[{case['id']}] Expected 200, got {resp.status_code}. Body: {resp.text[:300]}"
    )
    data = resp.json()
    # Required fields
    assert "classification" in data
    assert "risk_level" in data
    assert isinstance(data.get("risk_score"), (int, float))
    assert 0.0 <= data["risk_score"] <= 100.0
    assert "recommendation" in data


# ---------------------------------------------------------------------------
# Metric collection test
# ---------------------------------------------------------------------------

def test_url_detection_metrics_summary():
    """
    Run all URL cases and compute TP/TN/FP/FN.
    Writes a human-readable summary to stdout for capture in audit report.
    """
    tp = tn = fp = fn = 0
    errors = []

    for case in URL_TEST_CASES:
        resp = _post_url(case["url"])
        if resp.status_code != 200:
            errors.append(f"{case['id']}: HTTP {resp.status_code}")
            continue

        data = resp.json()
        is_safe = _is_safe_classification(data)
        expected_safe = case["expected_safe"]

        if expected_safe and is_safe:
            tn += 1
        elif expected_safe and not is_safe:
            fp += 1
        elif not expected_safe and not is_safe:
            tp += 1
        else:
            fn += 1

    total = tp + tn + fp + fn
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0

    print("\n" + "=" * 60)
    print("URL DETECTION RED-TEAM METRICS")
    print("=" * 60)
    print(f"  True  Positives (threat correctly flagged): {tp}")
    print(f"  True  Negatives (safe correctly cleared):   {tn}")
    print(f"  False Positives (safe incorrectly flagged): {fp}")
    print(f"  False Negatives (threat missed):            {fn}")
    print(f"  Total cases evaluated:                      {total}")
    print(f"  Precision:  {precision:.3f}")
    print(f"  Recall:     {recall:.3f}")
    print(f"  F1-Score:   {f1:.3f}")
    print(f"  FPR:        {fpr:.3f}")
    if errors:
        print(f"  Errors:     {errors}")
    print("=" * 60)

    # Basic sanity: at least 50% recall and precision
    assert recall >= 0.5, f"Recall too low: {recall:.3f} — model is missing too many threats"
    assert precision >= 0.5, f"Precision too low: {precision:.3f} — too many false alarms"
    assert f1 >= 0.5, f"F1 too low: {f1:.3f}"

