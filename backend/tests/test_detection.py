"""
Cyber Raksha AI - Stage 2 Threat Detection API Integration Tests
Tests real ML model inference, validation, edge cases, error handling,
database persistence, and status telemetry.
"""
import pytest
from fastapi.testclient import TestClient


def test_detection_status_endpoint(client: TestClient):
    """
    Verifies GET /api/v1/detection/status returns authentic model telemetry.
    Must confirm the real model is loaded and report true version.
    """
    response = client.get("/api/v1/detection/status")
    assert response.status_code == 200
    data = response.json()

    assert data["model_available"] is True
    assert data["model_loaded"] is True
    assert data["inference_status"] == "READY"
    assert "v1.0.0" in data["model_version"]
    assert data["algorithm"] in ["RandomForest", "GradientBoosting", "DecisionTree", "LogisticRegression"]


def test_legitimate_url_classification(client: TestClient):
    """
    Verifies that a well-known legitimate URL is analyzed by the real ML model
    and classified as LEGITIMATE with a low risk score.
    """
    response = client.post(
        "/api/v1/detection/url",
        json={"url": "https://www.google.com/search?q=cybersecurity"}
    )
    assert response.status_code == 200
    data = response.json()

    assert data["success"] is True
    assert data["classification"] == "LEGITIMATE"
    assert data["risk_level"] == "LOW"
    assert data["risk_score"] < 40.0
    assert "analysis" in data
    assert "features" in data["analysis"]
    assert len(data["analysis"]["features"]) >= 20
    assert data["model_version"] != "none"


def test_phishing_url_classification(client: TestClient):
    """
    Verifies that a deceptive credential-harvesting URL is detected by the model
    and classified as PHISHING with HIGH or CRITICAL risk.
    """
    suspicious_url = "http://account-verification-support.paypal.com.crypto-wallet-verify.net/security/login.php?session=update"
    response = client.post(
        "/api/v1/detection/url",
        json={"url": suspicious_url}
    )
    assert response.status_code == 200
    data = response.json()

    assert data["success"] is True
    assert data["classification"] in ["PHISHING", "SUSPICIOUS"]
    assert data["risk_level"] in ["HIGH", "CRITICAL", "SUSPICIOUS"]
    assert data["risk_score"] >= 40.0
    assert len(data["analysis"]["risk_indicators"]) > 0


def test_empty_url_validation_rejection(client: TestClient):
    """
    Verifies rejection of empty or blank URL input with HTTP 400.
    """
    response = client.post(
        "/api/v1/detection/url",
        json={"url": "   "}
    )
    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()


def test_malformed_url_handling(client: TestClient):
    """
    Verifies graceful handling of syntactically invalid URLs without crash.
    """
    response = client.post(
        "/api/v1/detection/url",
        json={"url": "not_a_valid_url_no_scheme_or_dots"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is False
    assert data["classification"] == "INVALID"
    assert "recommendation" in data


def test_excessive_url_length_rejection(client: TestClient):
    """
    Verifies DOS protection against oversized URLs exceeding 2048 chars.
    """
    oversized_url = "https://example.com/" + "a" * 2500
    response = client.post(
        "/api/v1/detection/url",
        json={"url": oversized_url}
    )
    assert response.status_code == 400
    assert "exceeds" in response.json()["detail"].lower()


def test_detection_history_recorded_in_db(client: TestClient):
    """
    Verifies that genuine analyses are saved to the SQLite database and queryable.
    """
    test_target = "https://wikipedia.org/wiki/Computer_security"
    # Execute analysis
    post_resp = client.post(
        "/api/v1/detection/url",
        json={"url": test_target}
    )
    assert post_resp.status_code == 200

    # Query history
    hist_resp = client.get("/api/v1/detection/history")
    assert hist_resp.status_code == 200
    hist_data = hist_resp.json()

    assert hist_data["total_records"] > 0
    records = hist_data["records"]
    matching = [r for r in records if "wikipedia.org" in r["target_identifier"]]
    assert len(matching) > 0
    assert matching[0]["module_code"] == "PHISHING"
    assert matching[0]["status"] == "COMPLETED"
