"""
Cyber Raksha AI - Stage 3 Communication Fraud Detection Tests
Verifies real NLP model inference, indicator extraction, Digital Arrest detection,
validation edge cases, database persistence, and system non-regression.
"""
import pytest
from fastapi.testclient import TestClient


def test_communication_status_endpoint(client: TestClient):
    """
    Verifies GET /api/v1/communication/status returns authentic model telemetry.
    """
    response = client.get("/api/v1/communication/status")
    assert response.status_code == 200
    data = response.json()

    assert data["model_available"] is True
    assert data["model_loaded"] is True
    assert data["inference_status"] == "READY"
    assert "LinearSVC" in data["algorithm"]
    assert "v1.0.0" in data["model_version"]
    assert data["metrics_summary"] is not None


def test_normal_personal_message(client: TestClient):
    """
    Test Case 1: Normal personal message should be classified as SAFE / LOW risk.
    """
    response = client.post(
        "/api/v1/communication/analyze",
        json={"message": "Hey Rahul, let's grab coffee tomorrow afternoon and discuss the project."}
    )
    assert response.status_code == 200
    data = response.json()

    assert data["success"] is True
    assert data["classification"] in ["SAFE", "INCONCLUSIVE"]
    assert data["risk_level"] == "LOW"
    assert data["risk_score"] < 40.0


def test_legitimate_banking_notification(client: TestClient):
    """
    Test Case 2: Standard non-coercive bank notification.
    """
    response = client.post(
        "/api/v1/communication/analyze",
        json={"message": "Your salary for October has been credited to your HDFC Bank account ending in 4012."}
    )
    assert response.status_code == 200
    data = response.json()

    assert data["success"] is True
    assert data["classification"] in ["SAFE", "INCONCLUSIVE", "SUSPICIOUS"]
    assert data["risk_score"] < 50.0


def test_promotional_spam_message(client: TestClient):
    """
    Test Case 3: Commercial lottery spam.
    """
    response = client.post(
        "/api/v1/communication/analyze",
        json={"message": "Congratulations! You won Rs 25,00,000 in Kaun Banega Crorepati lottery. WhatsApp manager now."}
    )
    assert response.status_code == 200
    data = response.json()

    assert data["success"] is True
    assert data["risk_score"] >= 40.0


def test_otp_theft_attempt(client: TestClient):
    """
    Test Case 5: OTP & banking credential theft attempt.
    """
    response = client.post(
        "/api/v1/communication/analyze",
        json={"message": "Your debit card is blocked immediately. Share your 6-digit OTP verification code to unblock."}
    )
    assert response.status_code == 200
    data = response.json()

    assert data["success"] is True
    assert data["classification"] in ["FINANCIAL_SCAM", "PHISHING"]
    assert data["risk_level"] in ["HIGH", "CRITICAL"]
    assert data["risk_score"] >= 70.0
    assert any("OTP" in ind or "Financial" in ind for ind in data["detected_indicators"])


def test_fake_police_impersonation(client: TestClient):
    """
    Test Case 6: Fake police & regulatory authority impersonation.
    """
    response = client.post(
        "/api/v1/communication/analyze",
        json={"message": "Notice from Delhi Police Cyber Crime Branch: Illegal activities detected on your phone. Action required immediately."}
    )
    assert response.status_code == 200
    data = response.json()

    assert data["success"] is True
    assert data["classification"] in ["IMPERSONATION", "DIGITAL_ARREST_SCAM", "PHISHING"]
    assert data["risk_level"] in ["HIGH", "CRITICAL"]
    assert data["risk_score"] >= 60.0


def test_digital_arrest_scam_detection(client: TestClient):
    """
    Test Case 7: Complex Digital Arrest scam message.
    """
    da_text = (
        "CBI POLICE NOTICE: Non-bailable arrest warrant issued against your Aadhaar card for money laundering. "
        "You are placed under Digital Arrest. Stay on video call immediately. Transfer Rs 2,00,000 to RBI verification account to prove innocence."
    )
    response = client.post(
        "/api/v1/communication/digital-arrest/analyze",
        json={"message": da_text}
    )
    assert response.status_code == 200
    data = response.json()

    assert data["success"] is True
    assert data["classification"] == "DIGITAL_ARREST_SCAM"
    assert data["risk_level"] == "CRITICAL"
    assert data["risk_score"] >= 85.0
    assert data["analysis"]["is_digital_arrest_candidate"] is True
    assert len(data["detected_indicators"]) >= 2
    assert any("video" in rec.lower() or "arrest" in rec.lower() for rec in data["recommendations"])


def test_financial_transfer_manipulation(client: TestClient):
    """
    Test Case 8: Urgent coercive financial transfer request.
    """
    response = client.post(
        "/api/v1/communication/analyze",
        json={"message": "URGENT: Electricity bill unpaid. Power disconnected tonight unless you transfer Rs 1,450 immediately to avoid fee."}
    )
    assert response.status_code == 200
    data = response.json()

    assert data["success"] is True
    assert data["risk_score"] >= 50.0


def test_empty_message_validation_rejection(client: TestClient):
    """
    Test Case 11: Empty message should be rejected with HTTP 400.
    """
    response = client.post(
        "/api/v1/communication/analyze",
        json={"message": "   "}
    )
    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()


def test_oversized_message_rejection(client: TestClient):
    """
    Test Case 12: Extremely long message exceeding 10,000 chars should be rejected.
    """
    huge_msg = "A" * 12000
    response = client.post(
        "/api/v1/communication/analyze",
        json={"message": huge_msg}
    )
    assert response.status_code == 400
    assert "exceeds" in response.json()["detail"].lower()


def test_communication_history_persistence_and_privacy_redaction(client: TestClient):
    """
    Verifies that analysis is logged to SQLite and personal credentials (OTP) are redacted.
    """
    sensitive_msg = "Your secret OTP is 948123 for bank account transfer. Share immediately."
    post_resp = client.post(
        "/api/v1/communication/analyze",
        json={"message": sensitive_msg}
    )
    assert post_resp.status_code == 200

    hist_resp = client.get("/api/v1/communication/history")
    assert hist_resp.status_code == 200
    hist_data = hist_resp.json()

    assert hist_data["total_records"] > 0
    records = hist_data["records"]
    matching = [r for r in records if "OTP" in r["target_identifier"]]
    assert len(matching) > 0
    # Verify OTP value itself is redacted
    assert "948123" not in matching[0]["target_identifier"]
    assert "[REDACTED_OTP]" in matching[0]["target_identifier"]

