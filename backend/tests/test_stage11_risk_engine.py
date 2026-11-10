"""
Stage 11 — Unified Risk Engine Adversarial Test Suite
Evaluates multi-vector synthesis, conflict resolution, corroboration boosting,
dilution prevention, and edge conditions in the intelligence engine.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)
BYPASS = {"x-test-bypass-rate-limit": "true"}


def test_high_risk_url_with_harmless_message_prevents_dilution():
    """
    Submitting a dangerous phishing URL alongside an innocent text message
    MUST NOT dilute the risk score to LOW or MEDIUM.
    The highest individual vector severity must dominate.
    """
    payload = {
        "url": "http://sbi-online.netbanking.update-kyc.phishtest.invalid/secure",
        "message": "Hi mom, I will be home for dinner around 7 PM."
    }
    resp = client.post("/api/v1/intel/unified/analyze", json=payload, headers=BYPASS)
    assert resp.status_code == 200
    data = resp.json()

    assert data["overall_risk_level"] in ("HIGH", "CRITICAL")
    assert data["overall_risk_score"] >= 70.0
    # Must report conflict / multi-vector findings
    assert data["modules"]["url_detection"] is not None
    assert data["modules"]["communication_threat"] is not None


def test_low_risk_url_with_high_risk_message_preserves_threat():
    """
    Submitting a legitimate URL alongside an extortion/digital arrest message
    must still trigger a CRITICAL/HIGH alert.
    """
    payload = {
        "url": "https://www.google.com/",
        "message": "CBI Headquarters: Non-bailable arrest warrant issued. Transfer Rs 2,00,000 security bond immediately."
    }
    resp = client.post("/api/v1/intel/unified/analyze", json=payload, headers=BYPASS)
    assert resp.status_code == 200
    data = resp.json()

    assert data["overall_risk_level"] in ("HIGH", "CRITICAL")
    assert data["overall_risk_score"] >= 60.0
    assert "Digital Arrest" in data["threat_category"] or "Communication" in data["threat_category"] or "Impersonation" in data["threat_category"]


def test_corroboration_boost_when_both_vectors_are_malicious():
    """
    When both URL and message independently exhibit fraud indicators,
    the engine should apply a corroboration boost and flag multi-vector synergy.
    """
    payload = {
        "url": "http://paypal.com.secure-login-verify.phishtest.invalid/account/confirm",
        "message": "Your PayPal account is suspended. Confirm your password and OTP immediately to unlock."
    }
    resp = client.post("/api/v1/intel/unified/analyze", json=payload, headers=BYPASS)
    assert resp.status_code == 200
    data = resp.json()

    assert data["overall_risk_level"] in ("HIGH", "CRITICAL")
    assert data["overall_risk_score"] >= 80.0
    assert data["is_corroborated"] is True
    assert len(data["corroboration_notes"]) > 0


def test_single_vector_url_only_handled_cleanly():
    """Submitting only a URL without message or audio should analyze without error."""
    payload = {"url": "https://github.com/"}
    resp = client.post("/api/v1/intel/unified/analyze", json=payload, headers=BYPASS)
    assert resp.status_code == 200
    data = resp.json()

    assert data["modules"]["url_detection"] is not None
    assert data["modules"]["communication_threat"] is None
    assert data["modules"]["audio_detection"] is None
    assert data["overall_risk_level"] == "LOW"


def test_single_vector_message_only_handled_cleanly():
    """Submitting only a message without URL should analyze without error."""
    payload = {"message": "Meeting scheduled for 3 PM in conference room B."}
    resp = client.post("/api/v1/intel/unified/analyze", json=payload, headers=BYPASS)
    assert resp.status_code == 200
    data = resp.json()

    assert data["modules"]["communication_threat"] is not None
    assert data["modules"]["url_detection"] is None
    assert data["overall_risk_level"] in ("LOW", "INCONCLUSIVE")


def test_conflict_notes_generated_on_disagreeing_vectors():
    """
    When one module flags HIGH and another flags LOW, the engine must document
    the disagreement in conflict_notes and explain uncertainty.
    """
    payload = {
        "url": "https://www.microsoft.com/en-us",
        "message": "Urgent police summons: You are under digital custody."
    }
    resp = client.post("/api/v1/intel/unified/analyze", json=payload, headers=BYPASS)
    assert resp.status_code == 200
    data = resp.json()

    assert "conflict_notes" in data
    assert isinstance(data["conflict_notes"], list)
    assert "explanation" in data

