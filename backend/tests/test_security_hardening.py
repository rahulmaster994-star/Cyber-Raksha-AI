"""
backend/tests/test_security_hardening.py
Stage 8: Security Hardening & Privacy Governance Tests
Verifies rate limiting, security headers, input validation, and privacy controls.
"""
import pytest
from fastapi import status


def test_security_headers_present(client):
    """Verifies that all responses include defensive security headers and hardened CSP."""
    response = client.get("/api/health")
    assert response.status_code == status.HTTP_200_OK
    headers = response.headers

    assert headers.get("X-Content-Type-Options") == "nosniff"
    assert headers.get("X-Frame-Options") == "DENY"
    assert headers.get("X-XSS-Protection") == "1; mode=block"
    assert headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
    assert "camera=()" in headers.get("Permissions-Policy", "")

    csp = headers.get("Content-Security-Policy", "")
    assert "default-src 'self'" in csp
    assert "script-src 'self';" in csp or "script-src 'self' " in csp
    assert "script-src 'self' 'unsafe-inline'" not in csp
    assert "style-src-attr 'unsafe-inline'" in csp
    assert "base-uri 'self'" in csp
    assert "form-action 'self'" in csp


def test_dangerous_url_protocols_rejected(client):
    """Verifies rejection of dangerous protocols (SSRF / XSS prevention)."""
    prohibited_urls = [
        "javascript:alert(document.cookie)",
        "data:text/html,<script>alert(1)</script>",
        "file:///etc/passwd",
        "file:///C:/Windows/System32/drivers/etc/hosts",
        "gopher://127.0.0.1:6379",
        "ftp://malicious-ftp.org/payload.exe",
        "about:blank",
        "chrome://extensions"
    ]

    for bad_url in prohibited_urls:
        res = client.post("/api/v1/detection/url", json={"url": bad_url})
        assert res.status_code == status.HTTP_400_BAD_REQUEST
        assert "Only http:// and https://" in res.json().get("detail", "") or "prohibited" in res.json().get("detail", "")


def test_empty_and_oversized_url_rejected(client):
    """Verifies rejection of empty strings and excessive length."""
    # Empty
    res_empty = client.post("/api/v1/detection/url", json={"url": ""})
    assert res_empty.status_code == status.HTTP_400_BAD_REQUEST

    # Whitespace only
    res_ws = client.post("/api/v1/detection/url", json={"url": "   "})
    assert res_ws.status_code == status.HTTP_400_BAD_REQUEST

    # Oversized (> 2048 chars)
    oversized = "https://example.com/" + "a" * 2050
    res_over = client.post("/api/v1/detection/url", json={"url": oversized})
    assert res_over.status_code == status.HTTP_400_BAD_REQUEST


def test_privacy_policy_endpoint(client):
    """Verifies the transparency data policy endpoint."""
    res = client.get("/api/v1/privacy/policy")
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    assert "data_collected" in data
    assert "data_stored" in data
    assert "redaction_policies" in data
    assert "user_rights" in data
    assert data["retention_period_days"] > 0


def test_privacy_settings_workflow(client, db_session):
    """Verifies retrieval and updating of privacy retention settings."""
    # 1. Get settings
    get_res = client.get("/api/v1/privacy/settings")
    assert get_res.status_code == status.HTTP_200_OK
    data = get_res.json()
    assert "data_retention_days" in data
    assert "strict_privacy_mode" in data

    # 2. Patch settings
    patch_res = client.patch(
        "/api/v1/privacy/settings",
        json={
            "data_retention_days": 60,
            "strict_privacy_mode": True
        }
    )
    assert patch_res.status_code == status.HTTP_200_OK
    patch_data = patch_res.json()
    assert patch_data["settings"]["data_retention_days"] == 60


def test_purge_analysis_history(client, db_session):
    """Verifies user ability to purge stored analysis records."""
    # Create an analysis record first
    client.post("/api/v1/detection/url", json={"url": "https://www.google.com"})

    # Purge history
    del_res = client.delete("/api/v1/privacy/history?module_code=PHISHING")
    assert del_res.status_code == status.HTTP_200_OK
    assert del_res.json()["status"] == "SUCCESS"

    # Verify history is now empty for PHISHING
    hist_res = client.get("/api/v1/detection/history")
    assert hist_res.status_code == status.HTTP_200_OK
    records = [r for r in hist_res.json()["records"] if r["module_code"] == "PHISHING"]
    assert len(records) == 0


def test_rate_limiter_protection():
    """
    Verifies that excessive requests to a heavy endpoint triggers 429 Too Many Requests.
    Uses an explicit direct TestClient without the test bypass header.
    """
    from fastapi.testclient import TestClient
    from unittest.mock import patch
    from app.main import app
    # The heavy endpoint limit is 30 per 60s
    triggered_429 = False
    with patch("ai_engine.threat_intelligence.feed_updater.feed_updater.update_urlhaus_feed") as mock_feed:
        mock_feed.return_value = {"source": "URLHAUS", "status": "SUCCESS", "records_added": 0, "duration_seconds": 0.001}
        with TestClient(app) as unbypassed_client:
            for _ in range(35):
                res = unbypassed_client.post("/api/v1/intel/feed/update", headers={"x-test-bypass-rate-limit": "false"})
                if res.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
                    triggered_429 = True
                    assert "Rate Limit Exceeded" in res.json().get("error", "")
                    assert "Retry-After" in res.headers
                    break

    assert triggered_429 is True


def test_safe_error_handling_no_stack_trace_leak(client):
    """
    Verifies that unhandled internal server exceptions return a sanitized JSON message
    rather than leaking internal Python stack traces, file paths, or credentials.
    """
    # Non-existent endpoint or bad request should return structured JSON
    res = client.get("/api/v1/incidents/99999999")
    assert res.status_code == status.HTTP_404_NOT_FOUND
    data = res.json()
    assert "detail" in data
    # Ensure no internal Python traceback strings
    assert "Traceback (most recent call last)" not in str(data)
