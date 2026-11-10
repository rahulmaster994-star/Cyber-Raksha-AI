"""
Stage 11 — Audio Deepfake Detection Red-Team Test Suite
Adversarial testing of audio ingestion, acoustic feature extraction,
file type validation, payload boundary controls, and model safety constraints.
All tests use in-memory synthetic WAV fixtures generated with standard library wave.
"""
import io
import math
import struct
import wave
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)
BYPASS = {"x-test-bypass-rate-limit": "true"}


def _generate_synthetic_wav(duration_s: float = 1.0, sample_rate: int = 16000, freq: float = 440.0) -> bytes:
    """Generates an in-memory mono PCM WAV buffer for safe testing."""
    num_samples = int(duration_s * sample_rate)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        raw_frames = bytearray()
        for i in range(num_samples):
            val = int(32767.0 * 0.5 * math.sin(2.0 * math.pi * freq * (i / sample_rate)))
            raw_frames.extend(struct.pack("<h", val))
        wf.writeframes(raw_frames)
    return buf.getvalue()


def _generate_corrupted_wav() -> bytes:
    """Generates invalid WAV header followed by garbage bytes."""
    return b"RIFF\x00\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00" + b"\xff" * 20


def test_audio_status_reports_correct_capabilities():
    """Verify audio status reports model algorithm and disclaims biometric identification."""
    resp = client.get("/api/v1/audio/status", headers=BYPASS)
    assert resp.status_code == 200
    data = resp.json()
    assert "model_available" in data
    assert "model_loaded" in data
    assert "model_type" in data
    # Must report acoustic classification, not biometric speaker identification
    assert "biometric" not in data.get("model_type", "").lower()
    assert "disclaimer" in data


def test_valid_synthetic_audio_inference():
    """Submit a valid synthetic WAV file and verify structured response."""
    wav_bytes = _generate_synthetic_wav(duration_s=1.5, sample_rate=16000, freq=300.0)
    files = {"file": ("test_synthetic.wav", io.BytesIO(wav_bytes), "audio/wav")}

    resp = client.post("/api/v1/audio/analyze", files=files, headers=BYPASS)
    assert resp.status_code == 200
    data = resp.json()

    assert "classification" in data
    assert "risk_level" in data
    assert "risk_score" in data
    assert isinstance(data["risk_score"], (int, float))
    assert 0.0 <= data["risk_score"] <= 100.0
    assert "audio_metadata" in data
    assert data["audio_metadata"]["sample_rate"] == 16000
    assert data["audio_metadata"]["duration_seconds"] >= 1.0


def test_corrupted_audio_file_rejection():
    """Submit a corrupted WAV file; API must reject or handle gracefully without 500 crash."""
    corrupt_bytes = _generate_corrupted_wav()
    files = {"file": ("corrupt.wav", io.BytesIO(corrupt_bytes), "audio/wav")}

    resp = client.post("/api/v1/audio/analyze", files=files, headers=BYPASS)
    # Accepts 400 Bad Request or 422 Unprocessable or 200 with success=False/INCONCLUSIVE
    assert resp.status_code in (200, 400, 422)
    if resp.status_code == 200:
        data = resp.json()
        assert data.get("success") is False or data.get("classification") in ("INCONCLUSIVE", "ERROR", "INVALID")


def test_non_audio_file_upload_rejected():
    """Submit an executable or text payload disguised as WAV."""
    fake_file = b"MZ\x90\x00\x03\x00\x00\x00\x04\x00\x00\x00\xff\xff\x00\x00"
    files = {"file": ("payload.exe", io.BytesIO(fake_file), "application/x-msdownload")}

    resp = client.post("/api/v1/audio/analyze", files=files, headers=BYPASS)
    assert resp.status_code in (400, 415, 422)


def test_empty_audio_file_rejected():
    """Submit 0-byte file; must be rejected with 400 or 422."""
    files = {"file": ("empty.wav", io.BytesIO(b""), "audio/wav")}
    resp = client.post("/api/v1/audio/analyze", files=files, headers=BYPASS)
    assert resp.status_code in (400, 422)


def test_audio_metadata_does_not_leak_biometrics():
    """Verify that response metadata contains acoustic features, NOT biometric PII."""
    wav_bytes = _generate_synthetic_wav(duration_s=1.0, sample_rate=16000, freq=440.0)
    files = {"file": ("sample.wav", io.BytesIO(wav_bytes), "audio/wav")}

    resp = client.post("/api/v1/audio/analyze", files=files, headers=BYPASS)
    assert resp.status_code == 200
    data = resp.json()

    # Ensure no biometric voiceprints or personal speaker profiles are returned
    resp_text = resp.text.lower()
    assert "speaker_id" not in resp_text
    assert "voiceprint" not in resp_text
    assert "biometric_template" not in resp_text
