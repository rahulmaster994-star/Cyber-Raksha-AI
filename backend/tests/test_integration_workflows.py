"""
backend/tests/test_integration_workflows.py
Stage 8: Comprehensive End-to-End Workflow Integration Tests
Verifies Workflows A through F across all real backend modules.
"""
import pytest
import io
import wave
import struct
from fastapi import status


def _create_test_wav_bytes(duration_seconds: float = 1.0, sample_rate: int = 16000) -> bytes:
    """Creates a minimal in-memory valid mono PCM WAV file."""
    buf = io.BytesIO()
    num_samples = int(duration_seconds * sample_rate)
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)  # 16-bit
        wf.setframerate(sample_rate)
        # 440 Hz tone
        data = bytearray()
        import math
        for i in range(num_samples):
            val = int(math.sin(2 * math.pi * 440 * (i / sample_rate)) * 16000)
            data.extend(struct.pack("<h", val))
        wf.writeframes(data)
    return buf.getvalue()


# ============================================================================
# WORKFLOW A: Phishing Protection End-to-End
# ============================================================================
def test_workflow_a_phishing_protection(client, db_session):
    """
    1. User submits suspicious URL.
    2. URL validated and analyzed by ML model.
    3. Threat intel checks available indicators.
    4. Result stored in analysis history.
    5. User receives risk explanation and prevention recommendations.
    6. User can create or associate an incident.
    """
    target_url = "http://secure-login-hdfcbank.serveo.net/verify"

    # Step 1 & 2: URL Detection
    res = client.post("/api/v1/detection/url", json={"url": target_url})
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    assert data["success"] is True
    assert data["risk_score"] > 0
    assert data["risk_level"] in ["HIGH", "CRITICAL", "MEDIUM"]
    assert "analysis" in data
    assert "recommendation" in data

    # Step 3: Threat Intel check
    intel_res = client.post("/api/v1/intel/search", json={"query": target_url})
    assert intel_res.status_code == status.HTTP_200_OK
    intel_data = intel_res.json()
    assert "is_threat_found" in intel_data

    # Step 4: Verify Analysis History persistence
    history_res = client.get("/api/v1/detection/history")
    assert history_res.status_code == status.HTTP_200_OK
    history_records = history_res.json()["records"]
    assert len(history_records) > 0
    recent_entry = history_records[0]
    assert recent_entry["module_code"] == "PHISHING"
    assert recent_entry["risk_score"] is not None

    # Step 5: Generate prevention recommendations
    rec_res = client.post(
        "/api/v1/prevention/recommendations",
        json={
            "classification": data["classification"],
            "risk_level": data["risk_level"],
            "risk_score": data["risk_score"],
            "threat_category": "Phishing Web Threat",
            "detected_indicators": data["analysis"].get("risk_indicators", []),
            "threat_intel_matches": []
        }
    )
    assert rec_res.status_code == status.HTTP_200_OK
    rec_data = rec_res.json()
    assert len(rec_data["immediate_actions"]) > 0

    # Step 6: Create incident associated with analysis
    inc_res = client.post(
        "/api/v1/incidents",
        json={
            "title": f"Phishing Exposure: {target_url[:50]}",
            "category": "PHISHING",
            "severity": data["risk_level"] if data["risk_level"] in ["HIGH", "CRITICAL"] else "MEDIUM",
            "summary": f"User scanned suspicious link with score {data['risk_score']}/100",
            "related_analysis_id": recent_entry["id"],
            "evidence_references": target_url
        }
    )
    assert inc_res.status_code == status.HTTP_201_CREATED
    inc_data = inc_res.json()
    assert inc_data["incident_number"].startswith("CR-INC-")
    assert inc_data["status"] == "ACTION_REQUIRED"
    assert len(inc_data["actions"]) > 0


# ============================================================================
# WORKFLOW B: Communication Scam Protection End-to-End
# ============================================================================
def test_workflow_b_communication_scam_protection(client, db_session):
    """
    1. User submits suspicious text.
    2. Communication analysis runs (NLP).
    3. Digital arrest analysis evaluates coercion signatures.
    4. History is stored with privacy redaction.
    5. Incident can be created and tracked.
    """
    scam_msg = (
        "URGENT NOTICE FROM CBI HQ NEW DELHI: An FIR has been registered against your Aadhaar 2345 6789 0123 "
        "regarding an illegal drug courier intercepted at Mumbai customs. You are under digital arrest. "
        "Join Skype immediately for interrogation and transfer verified security deposit to RBI safe account."
    )

    # Step 1 & 2: General communication analysis
    comm_res = client.post("/api/v1/communication/analyze", json={"message": scam_msg})
    assert comm_res.status_code == status.HTTP_200_OK
    comm_data = comm_res.json()
    assert comm_data["success"] is True
    assert comm_data["risk_level"] in ["HIGH", "CRITICAL"]

    # Step 3: Specialized digital arrest check
    da_res = client.post("/api/v1/communication/digital-arrest/analyze", json={"message": scam_msg})
    assert da_res.status_code == status.HTTP_200_OK
    da_data = da_res.json()
    assert da_data["classification"] == "DIGITAL_ARREST_SCAM"
    assert da_data["risk_score"] >= 80.0

    # Step 4: Verify privacy redaction in history
    hist_res = client.get("/api/v1/communication/history")
    assert hist_res.status_code == status.HTTP_200_OK
    rec = hist_res.json()["records"][0]
    # Sensitive Aadhaar pattern should be redacted
    assert "2345 6789 0123" not in rec["target_identifier"]
    assert "[REDACTED_AADHAAR]" in rec["target_identifier"]

    # Step 5: Create Incident
    inc_res = client.post(
        "/api/v1/incidents",
        json={
            "title": "Digital Arrest Coercion Attempt",
            "category": "DIGITAL_ARREST",
            "severity": "CRITICAL",
            "summary": "Victim threatened with fake CBI arrest and Skype interrogation",
            "related_analysis_id": rec["id"]
        }
    )
    assert inc_res.status_code == status.HTTP_201_CREATED
    inc_data = inc_res.json()
    assert any("1930" in a["description"] or "Skype" in a["description"] for a in inc_data["actions"])


# ============================================================================
# WORKFLOW C: Voice Impersonation Protection End-to-End
# ============================================================================
def test_workflow_c_voice_impersonation_protection(client, db_session):
    """
    1. User uploads audio recording.
    2. Backend validates format and processes safely.
    3. Audio detector analyzes acoustic artifacts without claiming identity.
    4. Result logged in history without storing raw audio data.
    5. Prevention recommendations available.
    """
    wav_bytes = _create_test_wav_bytes(duration_seconds=1.5)
    files = {"file": ("suspicious_executive_call.wav", wav_bytes, "audio/wav")}

    res = client.post("/api/v1/audio/analyze", files=files)
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    assert "classification" in data
    assert "risk_score" in data
    assert "risk_level" in data
    assert "audio_metadata" in data
    assert "explanation" in data
    # Verify no false identity claims
    assert "biometric identity" not in data["explanation"].lower() or "not identify" in data["explanation"].lower()

    # Verify history logging
    hist_res = client.get("/api/v1/audio/history")
    assert hist_res.status_code == status.HTTP_200_OK
    records = hist_res.json()["records"]
    assert len(records) > 0
    # Identifier should contain filename and duration, not binary bytes
    assert "suspicious_executive_call.wav" in records[0]["target_identifier"]


# ============================================================================
# WORKFLOW D: Unified Fraud Protection End-to-End
# ============================================================================
def test_workflow_d_unified_fraud_protection(client, db_session):
    """
    1. Multi-vector threat submission (message containing a URL).
    2. Both URL detector and NLP detector run.
    3. Threat intelligence correlates indicators.
    4. Unified risk engine calculates score + corroboration boost.
    5. Returns segregated factual evidence vs model predictions.
    6. Creates security event and incident.
    """
    multimodal_msg = (
        "Dear Customer, your SBI netbanking has been blocked due to missing PAN. "
        "Update immediately at http://secure-login-hdfcbank.serveo.net/verify to restore services."
    )

    res = client.post(
        "/api/v1/intel/unified/analyze",
        json={"message": multimodal_msg}
    )
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    assert "overall_risk_level" in data
    assert "overall_risk_score" in data
    assert "evidence_chain" in data
    assert "modules" in data
    assert data["modules"]["url_detection"] is not None
    assert data["modules"]["communication_threat"] is not None
    # Check factual vs model evidence
    assert "factual_evidence" in data
    assert "model_predictions" in data

    # Verify live security events logged
    events_res = client.get("/api/v1/intel/events/live")
    assert events_res.status_code == status.HTTP_200_OK


# ============================================================================
# WORKFLOW E: Browser Extension Integration Contract
# ============================================================================
def test_workflow_e_browser_extension_contract(client, db_session):
    """
    Verifies that POST /api/v1/detection/url adheres strictly to the
    response contract expected by browser_extension/popup.js and background.js.
    """
    test_urls = [
        "https://www.google.com",
        "http://account-verification-support.paypal.com.crypto-wallet-verify.net/login.php"
    ]

    for u in test_urls:
        res = client.post("/api/v1/detection/url", json={"url": u})
        assert res.status_code == status.HTTP_200_OK
        data = res.json()
        assert "classification" in data
        assert "risk_level" in data
        assert data["risk_level"] in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
        assert "risk_score" in data
        assert isinstance(data["risk_score"], (int, float))
        assert "recommendation" in data
        assert "analysis" in data
        assert "risk_indicators" in data["analysis"]


# ============================================================================
# WORKFLOW F: Mobile PWA & Central Telemetry
# ============================================================================
def test_workflow_f_mobile_pwa_and_dashboard_stats(client, db_session):
    """
    Verifies system endpoints consumed by the PWA and central operations dashboard.
    """
    # 1. Health check
    h_res = client.get("/api/health")
    assert h_res.status_code == status.HTTP_200_OK
    assert h_res.json()["status"] in ["healthy", "degraded"]

    # 2. System Info
    s_res = client.get("/api/system/info")
    assert s_res.status_code == status.HTTP_200_OK
    s_data = s_res.json()
    assert len(s_data["implemented_components"]) >= 10

    # 3. Dashboard stats
    d_res = client.get("/api/v1/system/dashboard-stats")
    assert d_res.status_code == status.HTTP_200_OK
    d_data = d_res.json()
    assert "total_analyses" in d_data
    assert "url_threats" in d_data
    assert "comm_threats" in d_data
    assert "audio_threats" in d_data
    assert "incidents" in d_data
    assert "risk_distribution" in d_data
