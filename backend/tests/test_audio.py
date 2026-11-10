"""
Tests for Stage 4: Voice Deepfake & Audio Impersonation Detection.
Verifies:
  - GET /api/v1/audio/status
  - POST /api/v1/audio/analyze (valid WAV upload, invalid format rejection, short audio)
  - GET /api/v1/audio/history
  - GET /api/v1/audio/analysis/{id}
"""
import io
import wave
import struct
import numpy as np
import pytest
from fastapi.testclient import TestClient


def make_test_wav_bytes(duration: float = 2.0, sample_rate: int = 16000) -> bytes:
    """Helper to synthesize valid in-memory 16-bit PCM WAV bytes."""
    n_samples = int(duration * sample_rate)
    # Generate 440 Hz sine wave + slight harmonics
    t = np.linspace(0, duration, n_samples)
    sig = 0.5 * np.sin(2 * np.pi * 440 * t) + 0.2 * np.sin(2 * np.pi * 880 * t)
    sig_int16 = (sig * 32767).astype(np.int16)

    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(sig_int16.tobytes())
    buf.seek(0)
    return buf.read()


def test_audio_status_endpoint(client: TestClient):
    """Ensure audio status reports model availability, format support, and loaded state."""
    response = client.get("/api/v1/audio/status")
    assert response.status_code == 200
    data = response.json()
    assert data["module"] == "VOICE_DETECT"
    assert data["model_available"] is True
    assert data["model_loaded"] is True
    assert data["stage"] == "STAGE_4"
    assert ".wav" in data["supported_formats"]
    assert "disclaimer" in data


def test_audio_analyze_valid_wav(client: TestClient):
    """Test analyzing a valid WAV audio file upload."""
    wav_bytes = make_test_wav_bytes(duration=2.0)
    files = {
        "file": ("sample_recording.wav", wav_bytes, "audio/wav")
    }
    response = client.post("/api/v1/audio/analyze", files=files)
    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "SUCCESS"
    assert data["classification"] in [
        "LIKELY_NATURAL",
        "POSSIBLY_MANIPULATED",
        "POTENTIALLY_AI_GENERATED",
        "POTENTIALLY_VOICE_CLONED",
        "INCONCLUSIVE"
    ]
    assert 0.0 <= data["risk_score"] <= 100.0
    assert 0.0 <= data["confidence"] <= 1.0
    assert "explanation" in data
    assert isinstance(data["recommendations"], list)
    assert len(data["recommendations"]) > 0
    assert data["audio_metadata"]["filename"] == "sample_recording.wav"
    assert data["audio_metadata"]["format"] == "WAV"


def test_audio_analyze_rejects_unsupported_format(client: TestClient):
    """Test that non-WAV formats (like .txt) are rejected with clear 400 error."""
    files = {
        "file": ("malicious.txt", b"plain text is not audio", "text/plain")
    }
    response = client.post("/api/v1/audio/analyze", files=files)
    assert response.status_code == 400
    assert "Unsupported format" in response.json()["detail"]


def test_audio_analyze_empty_file(client: TestClient):
    """Test handling of empty file upload."""
    files = {
        "file": ("empty.wav", b"", "audio/wav")
    }
    response = client.post("/api/v1/audio/analyze", files=files)
    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()


def test_audio_analyze_too_short(client: TestClient):
    """Test handling of very short audio (less than 0.5s)."""
    wav_bytes = make_test_wav_bytes(duration=0.2)
    files = {
        "file": ("short.wav", wav_bytes, "audio/wav")
    }
    response = client.post("/api/v1/audio/analyze", files=files)
    # Validator requires at least 0.5s
    assert response.status_code == 400
    assert "minimum 0.5s" in response.json()["detail"]


def test_audio_history_and_detail(client: TestClient):
    """Test that analyses are logged in DB and can be retrieved."""
    # 1. Trigger an analysis
    wav_bytes = make_test_wav_bytes(duration=1.5)
    files = {
        "file": ("test_call.wav", wav_bytes, "audio/wav")
    }
    post_resp = client.post("/api/v1/audio/analyze", files=files)
    assert post_resp.status_code == 200

    # 2. Check history
    hist_resp = client.get("/api/v1/audio/history?limit=10")
    assert hist_resp.status_code == 200
    hist_data = hist_resp.json()
    assert hist_data["total_records"] >= 1
    recent = hist_data["records"][0]
    assert recent["module_code"] == "VOICE_DETECT"

    # 3. Retrieve specific record
    record_id = recent["id"]
    detail_resp = client.get(f"/api/v1/audio/analysis/{record_id}")
    assert detail_resp.status_code == 200
    detail_data = detail_resp.json()
    assert detail_data["id"] == record_id
    assert detail_data["module_code"] == "VOICE_DETECT"

