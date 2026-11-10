"""
test_threat_intel.py — Stage 5
Comprehensive test suite verifying:
  1. GET /api/v1/intel/status
  2. POST /api/v1/intel/search (known malicious IoC, legitimate/benign query)
  3. GET /api/v1/intel/indicators
  4. POST /api/v1/intel/feed/update
  5. POST /api/v1/intel/unified/analyze:
     - Case A: Message with suspicious URL (corroborated)
     - Case B: Digital arrest coercion message
     - Case C: Clean message
  6. POST /api/v1/intel/unified/analyze-audio (multi-modal with voice upload)
  7. GET /api/v1/intel/events/live
"""
import io
import wave
import numpy as np
import pytest
from fastapi.testclient import TestClient


def make_test_wav_bytes(duration: float = 1.5, sample_rate: int = 16000) -> bytes:
    """Helper to synthesize valid in-memory WAV bytes."""
    n_samples = int(duration * sample_rate)
    t = np.linspace(0, duration, n_samples)
    sig = 0.5 * np.sin(2 * np.pi * 440 * t)
    sig_int16 = (sig * 32767).astype(np.int16)

    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(sig_int16.tobytes())
    buf.seek(0)
    return buf.read()


def test_intel_status_endpoint(client: TestClient):
    """Verify threat intelligence status returns active indicators and sources."""
    response = client.get("/api/v1/intel/status")
    assert response.status_code == 200
    data = response.json()
    assert data["module"] == "THREAT_INTEL"
    assert data["service_status"] == "OPERATIONAL"
    assert data["total_active_indicators"] >= 5
    assert "URLHAUS" in data["sources"]
    assert "PHISHTANK" in data["sources"]


def test_intel_search_known_malicious_domain(client: TestClient):
    """Verify searching a known malicious IoC returns threat metadata."""
    payload = {"query": "secure-login-hdfcbank.serveo.net"}
    response = client.post("/api/v1/intel/search", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["is_threat_found"] is True
    assert data["source"] == "PHISHTANK"
    assert data["severity"] == "CRITICAL"
    assert data["matched_indicator"]["threat_type"] == "PHISHING"


def test_intel_search_benign_domain(client: TestClient):
    """Verify searching a clean domain returns no threat found without false positives."""
    payload = {"query": "https://google.com"}
    response = client.post("/api/v1/intel/search", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["is_threat_found"] is False
    assert data["matched_indicator"] is None


def test_intel_list_indicators(client: TestClient):
    """Verify listing threat indicators returns structured schemas."""
    response = client.get("/api/v1/intel/indicators?limit=10")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    first = data[0]
    assert "indicator_type" in first
    assert "indicator_value" in first
    assert "source_name" in first


def test_intel_feed_update(client: TestClient):
    """Verify manual feed trigger returns status and logs execution."""
    response = client.post("/api/v1/intel/feed/update")
    assert response.status_code == 200
    data = response.json()
    assert data["source"] == "URLHAUS"
    assert data["status"] in ["SUCCESS", "OFFLINE_FALLBACK"]


def test_unified_analysis_message_with_phishing_url(client: TestClient):
    """
    Test Case A: Message containing a suspicious link.
    System extracts URL, runs Stage 2 & Stage 3, and correlates evidence.
    """
    payload = {
        "message": "Urgent! Your account is suspended. Verify immediately at http://secure-login-hdfcbank.serveo.net/login before legal action."
    }
    response = client.post("/api/v1/intel/unified/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["overall_risk_level"] in ["HIGH", "CRITICAL"]
    assert data["overall_risk_score"] >= 60.0
    assert len(data["extracted_indicators"]["urls"]) >= 1
    assert data["modules"]["url_detection"] is not None
    assert data["modules"]["communication_threat"] is not None
    # Corroborated because both URL & Communication vector confirm threat
    assert data["is_corroborated"] is True
    assert len(data["recommended_actions"]) > 0


def test_unified_analysis_digital_arrest_extortion(client: TestClient):
    """
    Test Case B: Coercive law enforcement digital arrest attempt.
    """
    payload = {
        "message": "CBI POLICE NOTICE: Non-bailable arrest warrant issued against your Aadhaar card for money laundering. You are placed under Digital Arrest. Stay on video call immediately. Transfer Rs 2,00,000 to RBI verification account to prove innocence.",
        "is_digital_arrest": True
    }
    response = client.post("/api/v1/intel/unified/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["overall_risk_level"] in ["HIGH", "CRITICAL"]
    assert "Digital Arrest" in data["threat_category"]
    assert any("1930" in rec or "cybercrime" in rec for rec in data["recommended_actions"])


def test_unified_analysis_clean_message(client: TestClient):
    """Verify benign everyday text yields low risk."""
    payload = {
        "message": "Hi Rahul, let us meet at the library around 4pm for the project discussion."
    }
    response = client.post("/api/v1/intel/unified/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["overall_risk_level"] == "LOW"
    assert data["overall_risk_score"] < 40.0


def test_unified_analysis_with_audio_upload(client: TestClient):
    """
    Test Case C: Voice sample upload with accompanying coercive message text.
    """
    wav_bytes = make_test_wav_bytes(duration=1.5)
    files = {
        "file": ("extortion_voicenote.wav", wav_bytes, "audio/wav")
    }
    data = {
        "message": "Send 50,000 rupees immediately to settle your court clearance fees."
    }
    response = client.post("/api/v1/intel/unified/analyze-audio", files=files, data=data)
    assert response.status_code == 200
    res_data = response.json()

    assert "overall_risk_level" in res_data
    assert res_data["modules"]["audio_detection"] is not None
    assert res_data["modules"]["communication_threat"] is not None


def test_live_threat_events_stream(client: TestClient):
    """Verify live security event feed retrieval."""
    response = client.get("/api/v1/intel/events/live")
    assert response.status_code == 200
    events = response.json()
    assert isinstance(events, list)
