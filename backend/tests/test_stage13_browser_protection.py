"""
backend/tests/test_stage13_browser_protection.py
Phase A1 Browser Extension Automated Declarative Net Request (DNR) & Threat Intel Integration Tests.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)
BYPASS = {"x-test-bypass-rate-limit": "true"}

SHARED_DOMAINS_SAMPLE = [
    "github.com", "drive.google.com", "dropbox.com", "vercel.app", "netlify.app"
]


class TestPhaseA1BrowserProtection:
    """Automated backend test coverage for Phase A1 browser extension integration."""

    def test_01_health_endpoint_for_extension_options(self):
        """Extension popup and options page test /api/health."""
        res = client.get("/api/health", headers=BYPASS)
        assert res.status_code == 200
        data = res.json()
        assert data.get("status") in ("healthy", "ok")

    def test_02_threat_indicators_endpoint_format(self):
        """GET /api/v1/intel/indicators must provide indicators compatible with rules_manager."""
        res = client.get("/api/v1/intel/indicators?limit=50", headers=BYPASS)
        assert res.status_code == 200
        indicators = res.json()
        assert isinstance(indicators, list)
        assert len(indicators) >= 5, "Database must have active verified indicators seeded."

        for item in indicators:
            assert "indicator_type" in item
            assert "indicator_value" in item
            assert item["indicator_type"] in ("URL", "DOMAIN", "IP")
            assert item.get("confidence_score", 0) >= 0.80, "Indicators must meet confidence threshold"
            assert item.get("severity") in ("CRITICAL", "HIGH", "MEDIUM")
            assert item.get("is_active") is True

    def test_03_no_naked_shared_domains_in_threat_feed(self):
        """Shared multi-tenant hosting platforms must never be registered as naked domain threats."""
        res = client.get("/api/v1/intel/indicators?limit=100", headers=BYPASS)
        assert res.status_code == 200
        indicators = res.json()

        for item in indicators:
            if item["indicator_type"] == "DOMAIN":
                domain = item["indicator_value"].lower().strip()
                assert domain not in SHARED_DOMAINS_SAMPLE, (
                    f"Shared hosting domain '{domain}' must not be a whole-domain threat indicator!"
                )

    def test_04_manual_context_menu_detection_url(self):
        """The existing context-menu URL detection endpoint must remain responsive and accurate."""
        test_phish = "http://sbi-online.netbanking.update-kyc.phishtest.invalid/secure"
        res = client.post("/api/v1/detection/url", json={"url": test_phish}, headers=BYPASS)
        assert res.status_code == 200
        data = res.json()
        assert data["classification"] in ("PHISHING", "CRITICAL_THREAT", "HIGH_RISK")
        assert data["risk_score"] >= 70.0
        assert "recommendation" in data

    def test_05_manual_context_menu_clears_safe_url(self):
        """Safe destinations checked via context-menu return LOW risk."""
        safe_url = "https://www.google.com/"
        res = client.post("/api/v1/detection/url", json={"url": safe_url}, headers=BYPASS)
        assert res.status_code == 200
        data = res.json()
        assert data["classification"] == "LEGITIMATE"
        assert data["risk_score"] < 25.0

    def test_06_ssrf_attempt_rejected(self):
        """SSRF attempts sent through extension scanner are rejected with HTTP 400."""
        ssrf_url = "http://127.0.0.1:8000/api/health"
        res = client.post("/api/v1/detection/url", json={"url": ssrf_url}, headers=BYPASS)
        assert res.status_code in (400, 422)

    def test_07_threat_feed_status_telemetry(self):
        """Status endpoint provides telemetry for extension options page."""
        res = client.get("/api/v1/intel/status", headers=BYPASS)
        assert res.status_code == 200
        data = res.json()
        assert "total_active_indicators" in data or "total_indicators" in data
        assert data.get("total_active_indicators", data.get("total_indicators", 0)) >= 1
