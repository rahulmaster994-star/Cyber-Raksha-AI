"""
backend/tests/test_controlled_fixtures.py
Stage 8: Controlled Test Fixtures
Tests the 12 specific controlled benchmark scenarios mandated by Stage 8.
"""
import pytest
import io
import wave
import struct
import math
from fastapi import status


def _make_wav(duration_s=1.0, freq=440, rate=16000):
    buf = io.BytesIO()
    samples = int(duration_s * rate)
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(rate)
        data = bytearray()
        for i in range(samples):
            v = int(math.sin(2 * math.pi * freq * (i / rate)) * 16000)
            data.extend(struct.pack("<h", v))
        wf.writeframes(data)
    return buf.getvalue()


# Scenario 1: Known phishing test URL
def test_scenario_01_known_phishing_url(client):
    url = "http://account-verification-support.paypal.com.crypto-wallet-verify.net/security/login.php?session=id"
    res = client.post("/api/v1/detection/url", json={"url": url})
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    assert data["classification"] in ["PHISHING", "SUSPICIOUS"]
    assert data["risk_level"] in ["HIGH", "CRITICAL"]
    assert data["risk_score"] >= 60.0


# Scenario 2: Legitimate test URL
def test_scenario_02_legitimate_url(client):
    url = "https://www.google.com/search?q=cybersecurity"
    res = client.post("/api/v1/detection/url", json={"url": url})
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    assert data["classification"] in ["LEGITIMATE", "SUSPICIOUS"]
    assert data["risk_level"] in ["LOW", "MEDIUM"]
    assert data["risk_score"] < 50.0


# Scenario 3: Unknown / neutral novel URL
def test_scenario_03_unknown_url(client):
    url = "https://internal-docs-portal-2026.org/getting-started"
    res = client.post("/api/v1/detection/url", json={"url": url})
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    assert data["classification"] in ["LEGITIMATE", "SUSPICIOUS", "PHISHING"]
    assert "risk_score" in data
    assert "recommendation" in data


# Scenario 4: Suspicious financial message
def test_scenario_04_suspicious_financial_message(client):
    msg = "Your electricity power will be disconnected tonight at 9:30 PM. Call immediately at 9876543210 and pay pending bill via GooglePay."
    res = client.post("/api/v1/communication/analyze", json={"message": msg})
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    assert data["risk_score"] >= 40.0
    assert len(data["detected_indicators"]) > 0


# Scenario 5: Digital-arrest scam test message
def test_scenario_05_digital_arrest_scam_message(client):
    msg = (
        "CBI POLICE WARRANT: Illegal parcel containing passports and contraband seized at customs. "
        "A warrant is issued against your Aadhaar. Connect immediately on WhatsApp video call to avoid physical arrest."
    )
    res = client.post("/api/v1/communication/digital-arrest/analyze", json={"message": msg})
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    assert data["classification"] in ["DIGITAL_ARREST_SCAM", "IMPERSONATION"]
    assert data["risk_score"] >= 70.0
    assert len(data["detected_indicators"]) > 0


# Scenario 6: Harmless benign communication
def test_scenario_06_harmless_communication(client):
    msg = "Hey Rahul, let's meet tomorrow at 4 PM for coffee at the cafe near the park."
    res = client.post("/api/v1/communication/analyze", json={"message": msg})
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    assert data["classification"] in ["SAFE", "INCONCLUSIVE"]
    assert data["risk_level"] == "LOW"
    assert data["risk_score"] < 40.0


# Scenario 7: Available genuine audio test sample
def test_scenario_07_valid_audio_sample(client):
    wav = _make_wav(duration_s=1.2, freq=220)
    files = {"file": ("normal_speech_tone.wav", wav, "audio/wav")}
    res = client.post("/api/v1/audio/analyze", files=files)
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    assert data["audio_metadata"]["duration_seconds"] >= 1.0
    assert "risk_score" in data


# Scenario 8: Invalid audio file
def test_scenario_08_invalid_audio_file(client):
    # Reject non-WAV format
    files = {"file": ("malicious_executable.exe", b"MZ\x90\x00\x03\x00\x00\x00", "application/octet-stream")}
    res = client.post("/api/v1/audio/analyze", files=files)
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert "Only WAV files are supported" in res.json().get("detail", "") or "Unsupported" in res.json().get("detail", "")


# Scenario 9: Missing / unpopulated threat intelligence query
def test_scenario_09_missing_threat_intel(client):
    # Search an indicator not in threat feeds
    res = client.post("/api/v1/intel/search", json={"query": "https://unknown-internal-site-random12345.com"})
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    assert data["is_threat_found"] is False
    assert data["matched_indicator"] is None
    # Graceful handling without failure
    assert data["severity"] == "LOW"


# Scenario 10: Conflicting or inconclusive evidence handling
def test_scenario_10_conflict_resolution(client):
    """
    Submits a message with zero threat indicators and asks unified analyzer.
    Checks that evidence chain notes lack of external matches honestly.
    """
    res = client.post(
        "/api/v1/intel/unified/analyze",
        json={"message": "Good morning team, please find the quarterly report attached."}
    )
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    assert data["overall_risk_level"] == "LOW"
    assert "limitations" in data
    assert len(data["limitations"]) > 0


# Scenario 11: Backend health & degraded status reporting
def test_scenario_11_health_reporting(client):
    res = client.get("/api/health")
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    assert "status" in data
    assert "database_connected" in data
    assert "uptime_seconds" in data
    assert data["uptime_seconds"] >= 0


# Scenario 12: Incident creation, action completion, and resolution
def test_scenario_12_incident_lifecycle(client, db_session):
    # 1. Create incident
    c_res = client.post(
        "/api/v1/incidents",
        json={
            "title": "Suspected Credential Leak",
            "category": "ACCOUNT_COMPROMISE",
            "severity": "HIGH",
            "summary": "Employee reported entering banking password on fake link."
        }
    )
    assert c_res.status_code == status.HTTP_201_CREATED
    inc_data = c_res.json()
    inc_id = inc_data["id"]

    # 2. Complete an action if actions were populated
    if inc_data["actions"]:
        action_id = inc_data["actions"][0]["id"]
        act_res = client.post(f"/api/v1/prevention/actions/{action_id}/complete")
        assert act_res.status_code == status.HTTP_200_OK
        assert act_res.json()["is_completed"] is True

    # 3. Update status to RESOLVED
    up_res = client.patch(
        f"/api/v1/incidents/{inc_id}",
        json={
            "status": "RESOLVED",
            "resolution_notes": "Password changed and 2FA reset by user."
        }
    )
    assert up_res.status_code == status.HTTP_200_OK
    assert up_res.json()["status"] == "RESOLVED"
    assert up_res.json()["resolution_notes"] is not None
