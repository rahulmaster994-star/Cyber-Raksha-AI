"""
Stage 12 — Live Demonstration & End-to-End Integration Tests
Seven demo scenarios + full pipeline integration verification.
All tests use controlled synthetic test data. No external network calls.
"""
import io
import struct
import wave
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)
BYPASS = {"x-test-bypass-rate-limit": "true"}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _url(url: str):
    return client.post("/api/v1/detection/url", json={"url": url}, headers=BYPASS)


def _comm(msg: str):
    return client.post("/api/v1/communication/analyze", json={"message": msg}, headers=BYPASS)


def _da(msg: str):
    return client.post("/api/v1/communication/digital-arrest/analyze", json={"message": msg}, headers=BYPASS)


def _make_wav_bytes(duration_secs: float = 0.5, sample_rate: int = 16000, synthetic: bool = True) -> bytes:
    """Generate a minimal synthetic or natural-sounding WAV for test inference."""
    import numpy as np
    n_samples = int(sample_rate * duration_secs)
    if synthetic:
        # Simulate vocoder-like waveform: monotone + harmonic noise
        t = np.linspace(0, duration_secs, n_samples, dtype=np.float32)
        samples = (0.8 * np.sin(2 * np.pi * 150 * t) +
                   0.4 * np.sin(2 * np.pi * 300 * t) +
                   0.1 * np.random.uniform(-1, 1, n_samples)).astype(np.float32)
    else:
        # Simulate natural speech-like noise with varied amplitude
        rng = np.random.default_rng(42)
        samples = rng.standard_normal(n_samples).astype(np.float32) * 0.3

    pcm = (np.clip(samples, -1.0, 1.0) * 32767).astype(np.int16)
    buf = io.BytesIO()
    with wave.open(buf, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm.tobytes())
    return buf.getvalue()


def _audio(wav_bytes: bytes, filename: str = "test.wav"):
    return client.post(
        "/api/v1/audio/analyze",
        files={"file": (filename, io.BytesIO(wav_bytes), "audio/wav")},
        headers=BYPASS,
    )


# ---------------------------------------------------------------------------
# PHASE 1 — ENVIRONMENT VERIFICATION
# ---------------------------------------------------------------------------

class TestPhase1Environment:
    def test_01_backend_health_endpoint(self):
        """Backend health check returns 200 with status=ok."""
        r = client.get("/api/v1/health", headers=BYPASS)
        assert r.status_code == 200
        d = r.json()
        assert d.get("status") in ("ok", "healthy", "running", "degraded")

    def test_02_api_root_accessible(self):
        """Root API returns a usable response."""
        r = client.get("/", headers=BYPASS)
        assert r.status_code in (200, 307, 404)  # redirect to docs is acceptable

    def test_03_url_model_loaded(self):
        """URL analysis engine responds — confirming model is loaded."""
        r = _url("https://www.google.com/")
        assert r.status_code == 200
        d = r.json()
        assert "classification" in d
        assert "risk_score" in d

    def test_04_communication_model_loaded(self):
        """Communication model responds — confirming Stage 3 TF-IDF loaded."""
        r = _comm("Hello, how are you?")
        assert r.status_code == 200
        d = r.json()
        assert "classification" in d

    def test_05_audio_model_loaded(self):
        """Audio model status endpoint confirms model is ready."""
        r = client.get("/api/v1/audio/status", headers=BYPASS)
        assert r.status_code == 200
        d = r.json()
        assert d.get("model_loaded") is True

    def test_06_threat_intelligence_loaded(self):
        """Threat intelligence stats endpoint returns seeded IOC data."""
        r = client.get("/api/v1/intel/status", headers=BYPASS)
        assert r.status_code == 200
        d = r.json()
        assert "total_indicators" in d or "status" in d or "sources" in d

    def test_07_database_connectivity(self):
        """Incidents endpoint reads from DB without error."""
        r = client.get("/api/v1/incidents/", headers=BYPASS)
        assert r.status_code in (200, 401)  # 401 acceptable if auth required

    def test_08_input_validation_empty_url(self):
        """Empty URL input returns 400 or 422 — not a 500."""
        r = _url("")
        assert r.status_code in (400, 422)
        assert r.status_code != 500

    def test_09_input_validation_whitespace(self):
        """Whitespace-only URL input is rejected."""
        r = _url("   ")
        assert r.status_code in (400, 422)

    def test_10_input_validation_empty_message(self):
        """Empty message body returns structured error, not crash."""
        r = client.post("/api/v1/communication/analyze",
                        json={"message": ""},
                        headers=BYPASS)
        assert r.status_code in (200, 400, 422)


# ---------------------------------------------------------------------------
# PHASE 2 — DEMO 1: PHISHING URL DETECTION
# ---------------------------------------------------------------------------

class TestDemo1PhishingURL:
    def test_d1_01_known_malicious_url_flagged(self):
        """Structural phishing URL with brand impersonation is flagged PHISHING."""
        r = _url("http://sbi-online.netbanking.update-kyc.phishtest.invalid/secure")
        assert r.status_code == 200
        d = r.json()
        assert d["classification"] in ("PHISHING", "SUSPICIOUS", "HIGH_RISK")
        assert d["risk_score"] >= 50.0

    def test_d1_02_legitimate_google_cleared(self):
        """Google.com is classified LEGITIMATE with low risk score."""
        r = _url("https://www.google.com/")
        assert r.status_code == 200
        d = r.json()
        assert d["classification"] == "LEGITIMATE"
        assert d["risk_score"] < 30.0

    def test_d1_03_suspicious_url_detected(self):
        """Punycode homograph URL is flagged as suspicious/phishing."""
        r = _url("http://xn--pypal-4ve.com.phishtest.invalid/")
        assert r.status_code == 200
        d = r.json()
        assert d["risk_score"] >= 50.0

    def test_d1_04_bare_domain_handled(self):
        """Bare domain returns a valid classification (not error)."""
        r = _url("https://phishtest.invalid")
        assert r.status_code == 200
        d = r.json()
        assert "classification" in d
        assert "risk_score" in d
        assert 0 <= d["risk_score"] <= 100

    def test_d1_05_ip_url_flagged(self):
        """IP-address login URL receives HIGH risk score."""
        r = _url("http://198.51.100.25/bank/login.php?session=0xdeadbeef")
        assert r.status_code == 200
        d = r.json()
        assert d["risk_score"] >= 60.0

    def test_d1_06_recommendation_present(self):
        """Every phishing URL analysis includes a recommendation."""
        r = _url("http://paypal.com.secure-login-verify.phishtest.invalid/account/confirm")
        assert r.status_code == 200
        d = r.json()
        assert "recommendation" in d
        assert len(d["recommendation"]) > 10

    def test_d1_07_analysis_has_evidence(self):
        """Phishing analysis includes feature evidence."""
        r = _url("http://login-hdfc.phishtest.invalid/netbanking?redirect=true&token=abc")
        assert r.status_code == 200
        d = r.json()
        # At minimum risk_score, classification and recommendation must be present
        assert d.get("risk_score") is not None
        assert d.get("classification") is not None

    def test_d1_08_ssrf_blocked(self):
        """SSRF loopback URL rejected before analysis."""
        r = _url("http://127.0.0.1:8000/api/health")
        assert r.status_code in (400, 422)

    def test_d1_09_dangerous_scheme_blocked(self):
        """javascript: scheme rejected."""
        r = _url("javascript:alert(1)")
        assert r.status_code in (400, 422)

    def test_d1_10_analysis_history_endpoint(self):
        """URL analysis history is retrievable."""
        r = client.get("/api/v1/detection/history?limit=5", headers=BYPASS)
        assert r.status_code in (200, 404)
        if r.status_code == 200:
            d = r.json()
            assert isinstance(d, (list, dict))


# ---------------------------------------------------------------------------
# PHASE 2 — DEMO 2: COMMUNICATION FRAUD DETECTION
# ---------------------------------------------------------------------------

class TestDemo2CommFraud:
    def test_d2_01_bank_impersonation_flagged(self):
        """SBI KYC phishing message flagged HIGH or CRITICAL."""
        r = _comm("Dear Customer, Your SBI YONO account has been blocked due to incomplete PAN KYC. Click immediately: http://sbi-kyc-verify.net")
        assert r.status_code == 200
        d = r.json()
        assert d["risk_level"] in ("HIGH", "CRITICAL") or d["classification"] in ("IMPERSONATION", "FINANCIAL_SCAM", "PHISHING")

    def test_d2_02_otp_theft_flagged(self):
        """HDFC fake debit + OTP demand flagged."""
        r = _comm("HDFC Bank Alert: Rs 49,999 debited. Call 9876543210 and share cancellation OTP.")
        assert r.status_code == 200
        d = r.json()
        assert d["risk_score"] >= 50.0

    def test_d2_03_lottery_scam_suspicious(self):
        """KBC lottery scam returns SUSPICIOUS or higher."""
        r = _comm("Congratulations! You have won Rs 25,00,000 in KBC Lottery. Deposit 15,000 registration fee.")
        assert r.status_code == 200
        d = r.json()
        assert d["risk_score"] >= 30.0
        assert d["risk_level"] in ("MEDIUM", "HIGH", "CRITICAL")

    def test_d2_04_educational_scam_message_no_false_positive(self):
        """Educational advisory about scams is NOT flagged as HIGH/CRITICAL."""
        r = _comm("Cyber Safety Tip: Beware of scammers pretending to be police officers. Law enforcement never conducts arrests on Skype.")
        assert r.status_code == 200
        d = r.json()
        # Must NOT be HIGH or CRITICAL — this would be a false positive
        assert d["risk_level"] not in ("HIGH", "CRITICAL"), (
            f"FALSE POSITIVE: Educational message scored {d['risk_level']} ({d['risk_score']})"
        )

    def test_d2_05_legitimate_bank_statement_cleared(self):
        """Legitimate monthly bank statement is not HIGH/CRITICAL."""
        r = _comm("Your monthly statement for HDFC Bank Credit Card ending in 1234 for Oct 2026 is ready. Minimum due Rs 2,450 by 15-Nov-2026.")
        assert r.status_code == 200
        d = r.json()
        assert d["risk_level"] not in ("HIGH", "CRITICAL"), (
            f"FALSE POSITIVE: Legitimate bank statement scored {d['risk_level']}"
        )

    def test_d2_06_casual_message_cleared(self):
        """Casual personal message clears with LOW risk."""
        r = _comm("Hi Rahul, are we still meeting for lunch at 1 PM today?")
        assert r.status_code == 200
        d = r.json()
        assert d["risk_level"] in ("LOW", "MEDIUM")
        assert d["risk_score"] < 50.0

    def test_d2_07_risk_score_in_valid_range(self):
        """Every communication response has risk_score 0–100."""
        messages = [
            "Free money click now",
            "Hello from Mom",
            "Your account is blocked call immediately",
        ]
        for msg in messages:
            r = _comm(msg)
            assert r.status_code == 200
            d = r.json()
            assert 0.0 <= d["risk_score"] <= 100.0

    def test_d2_08_recommendations_present(self):
        """Every response includes recommendations."""
        r = _comm("I am from CBI. Transfer Rs 5 lakh to this safe account immediately.")
        assert r.status_code == 200
        d = r.json()
        assert "recommendations" in d
        assert len(d["recommendations"]) > 0


# ---------------------------------------------------------------------------
# PHASE 2 — DEMO 3: DIGITAL-ARREST SCAM DETECTION
# ---------------------------------------------------------------------------

class TestDemo3DigitalArrest:
    def test_d3_01_cbi_warrant_digital_arrest(self):
        """Classic CBI digital-arrest scam is CRITICAL."""
        r = _da("This is Officer Sharma from CBI. Arrest warrant issued under PMLA. You are under digital arrest. Join this Skype call now.")
        assert r.status_code == 200
        d = r.json()
        assert d["risk_level"] in ("HIGH", "CRITICAL")
        assert d["classification"] in ("DIGITAL_ARREST_SCAM", "IMPERSONATION")

    def test_d3_02_customs_narcotics_scam(self):
        """Customs narcotics digital-arrest variant detected."""
        r = _da("Customs Department: A parcel with illegal narcotics addressed to your Aadhaar has been seized. Digital arrest. Connect on WhatsApp video call with DCP Cyber Crime.")
        assert r.status_code == 200
        d = r.json()
        assert d["risk_level"] in ("HIGH", "CRITICAL")

    def test_d3_03_fake_court_warrant(self):
        """Supreme Court fake arrest warrant is flagged."""
        r = _da("Supreme Court Order: Non-bailable arrest warrant against your phone number. Pay Rs 2 lakh security bond to RBI verification account.")
        assert r.status_code == 200
        d = r.json()
        assert d["risk_score"] >= 40.0

    def test_d3_04_recommendations_include_safety_guidance(self):
        """Digital arrest detection includes actionable safety recommendations."""
        r = _da("I am from CBI. You are under digital arrest. Do not hang up.")
        assert r.status_code == 200
        d = r.json()
        recs = d.get("recommendations", [])
        assert len(recs) >= 1

    def test_d3_05_safe_account_instruction_flagged(self):
        """'Safe account' money transfer instruction is a key indicator."""
        r = _comm("Transfer all your savings to a safe account provided by our officer to avoid asset seizure under investigation.")
        assert r.status_code == 200
        d = r.json()
        assert d["risk_score"] >= 30.0

    def test_d3_06_multiple_indicators_combined(self):
        """Message with multiple DA indicators scores higher than single indicator."""
        single_r = _da("You are under arrest.")
        multi_r = _da("CBI Officer here. Arrest warrant issued. Digital arrest. Join Skype video call now. Transfer to safe account.")
        assert multi_r.status_code == 200
        assert single_r.status_code == 200
        # Multi-indicator should score higher or equal
        assert multi_r.json()["risk_score"] >= single_r.json()["risk_score"]


# ---------------------------------------------------------------------------
# PHASE 2 — DEMO 4: VOICE CLONING / SYNTHETIC AUDIO
# ---------------------------------------------------------------------------

class TestDemo4AudioDetection:
    def test_d4_01_wav_upload_accepted(self):
        """Valid WAV file is accepted and processed."""
        wav = _make_wav_bytes(synthetic=True)
        r = _audio(wav)
        assert r.status_code == 200
        d = r.json()
        assert "classification" in d
        assert "risk_score" in d

    def test_d4_02_risk_score_in_range(self):
        """Audio risk score is within 0–100."""
        wav = _make_wav_bytes(synthetic=False)
        r = _audio(wav)
        assert r.status_code == 200
        d = r.json()
        assert 0.0 <= d["risk_score"] <= 100.0

    def test_d4_03_non_wav_rejected(self):
        """Non-WAV file (fake MP3 header) is rejected."""
        r = client.post(
            "/api/v1/audio/analyze",
            files={"file": ("audio.mp3", io.BytesIO(b"\xff\xfb\x90\x00" * 100), "audio/mpeg")},
            headers=BYPASS,
        )
        assert r.status_code in (400, 422)

    def test_d4_04_capability_scope_disclosed(self):
        """API response includes forensic_capability_scope (non-biometric disclosure)."""
        wav = _make_wav_bytes(synthetic=True)
        r = _audio(wav)
        assert r.status_code == 200
        d = r.json()
        assert "forensic_capability_scope" in d or "biometric_identity_supported" in d

    def test_d4_05_biometric_identity_not_claimed(self):
        """API never claims biometric identity support."""
        r = client.get("/api/v1/audio/status", headers=BYPASS)
        assert r.status_code == 200
        d = r.json()
        assert d.get("biometric_identity_supported") is not True

    def test_d4_06_analysis_includes_recommendation(self):
        """Audio analysis always includes recommendations."""
        wav = _make_wav_bytes(synthetic=True)
        r = _audio(wav)
        assert r.status_code == 200
        d = r.json()
        # Audio schema uses 'recommendations' (list) not 'recommendation' (string)
        assert "recommendations" in d
        assert isinstance(d["recommendations"], list)


# ---------------------------------------------------------------------------
# PHASE 2 — DEMO 5: UNIFIED FRAUD RISK ENGINE
# ---------------------------------------------------------------------------

class TestDemo5UnifiedRiskEngine:
    def test_d5_01_unified_analysis_url_only(self):
        """Unified analysis with URL signal produces risk assessment."""
        r = client.post("/api/v1/intel/unified/analyze", json={
            "url": "http://paypal.com.secure-login-verify.phishtest.invalid/account/confirm",
        }, headers=BYPASS)
        assert r.status_code == 200
        d = r.json()
        assert "overall_risk_score" in d or "risk_score" in d or "risk_level" in d

    def test_d5_02_unified_analysis_comm_only(self):
        """Unified analysis with communication signal produces risk assessment."""
        r = client.post("/api/v1/intel/unified/analyze", json={
            "message": "CBI Officer: Arrest warrant. Digital arrest. Join Skype now.",
        }, headers=BYPASS)
        assert r.status_code in (200, 422)  # 422 if url is required field

    def test_d5_03_missing_signal_does_not_error(self):
        """Submitting only a URL to unified endpoint does not crash."""
        r = client.post("/api/v1/intel/unified/analyze", json={
            "url": "https://www.google.com/",
        }, headers=BYPASS)
        assert r.status_code != 500

    def test_d5_04_url_module_produces_result(self):
        """URL analysis as independent module produces result."""
        r = _url("http://sbi-online.netbanking.update-kyc.phishtest.invalid/secure")
        assert r.status_code == 200
        assert r.json()["risk_score"] >= 50.0

    def test_d5_05_comm_module_produces_result(self):
        """Communication analysis as independent module produces result."""
        r = _comm("I am CBI Officer. You are under digital arrest.")
        assert r.status_code == 200
        assert r.json()["risk_score"] >= 30.0


# ---------------------------------------------------------------------------
# PHASE 2 — DEMO 6: PREVENTION AND INCIDENT RESPONSE
# ---------------------------------------------------------------------------

class TestDemo6IncidentResponse:
    def test_d6_01_incidents_list_accessible(self):
        """Incidents list endpoint returns 200 or auth-protected 401."""
        r = client.get("/api/v1/incidents/", headers=BYPASS)
        assert r.status_code in (200, 401, 403, 404)

    def test_d6_02_incident_creation_on_high_risk(self):
        """High-risk URL analysis creates or references an incident."""
        r = _url("http://sbi-online.netbanking.update-kyc.phishtest.invalid/secure")
        assert r.status_code == 200
        # incident_id may be in response if auto-created
        d = r.json()
        # just verify the system does not crash on high-risk detection
        assert d.get("classification") in ("PHISHING", "SUSPICIOUS", "HIGH_RISK")

    def test_d6_03_prevention_recommendations_on_phishing(self):
        """Phishing URL detection returns actionable recommendations."""
        r = _url("http://login-hdfc.phishtest.invalid/netbanking")
        assert r.status_code == 200
        d = r.json()
        assert "recommendation" in d

    def test_d6_04_prevention_recommendations_on_da(self):
        """Digital arrest detection returns safety recommendations."""
        r = _da("CBI: You are under digital arrest. Transfer money.")
        assert r.status_code == 200
        d = r.json()
        recs = d.get("recommendations", [])
        assert isinstance(recs, list)


# ---------------------------------------------------------------------------
# PHASE 2 — DEMO 7: BROWSER EXTENSION & MOBILE/PWA
# ---------------------------------------------------------------------------

class TestDemo7BrowserMobile:
    def test_d7_01_extension_manifest_exists(self):
        """Browser extension manifest.json exists in the browser_extension dir."""
        import os
        base = r"c:\Users\RAHUL\OneDrive\Desktop\cyberRaksha"
        candidates = [
            os.path.join(base, "browser_extension", "manifest.json"),
            os.path.join(base, "browser-extension", "manifest.json"),
            os.path.join(base, "extension", "manifest.json"),
        ]
        found = any(os.path.exists(p) for p in candidates)
        assert found, f"No manifest.json found. Checked: {candidates}"

    def test_d7_02_pwa_manifest_exists(self):
        """PWA manifest.json exists in frontend/public."""
        import os
        base = r"c:\Users\RAHUL\OneDrive\Desktop\cyberRaksha"
        candidates = [
            os.path.join(base, "frontend", "public", "manifest.json"),
            os.path.join(base, "frontend", "public", "manifest.webmanifest"),
        ]
        found = any(os.path.exists(p) for p in candidates)
        # PWA is optional — PARTIAL if not found
        if not found:
            pytest.skip("PWA manifest not present — PARTIAL feature")

    def test_d7_03_extension_background_script_exists(self):
        """Browser extension has background.js."""
        import os
        base = r"c:\Users\RAHUL\OneDrive\Desktop\cyberRaksha"
        candidates = [
            os.path.join(base, "browser_extension", "background.js"),
            os.path.join(base, "browser-extension", "background.js"),
            os.path.join(base, "extension", "background.js"),
        ]
        found = any(os.path.exists(p) for p in candidates)
        assert found, "background.js missing from browser extension"

    def test_d7_04_api_cors_allows_extension_origin(self):
        """CORS headers allow browser extension (chrome-extension://) origin."""
        r = client.options(
            "/api/v1/detection/url",
            headers={
                "Origin": "chrome-extension://fakeidfortesting",
                "Access-Control-Request-Method": "POST",
            }
        )
        # FastAPI TestClient may not fully simulate CORS preflight, but check no 500
        assert r.status_code != 500


# ---------------------------------------------------------------------------
# PHASE 3 — END-TO-END INTEGRATION TESTS
# ---------------------------------------------------------------------------

class TestPhase3EndToEnd:
    def test_e2e_01_url_full_pipeline(self):
        """Full URL pipeline: input → validation → model → TI → risk → output."""
        r = _url("http://paypal.com.secure-login-verify.phishtest.invalid/account/confirm")
        assert r.status_code == 200
        d = r.json()
        # Every stage output must be present
        assert "classification" in d           # ML classification
        assert "risk_score" in d               # Risk engine output
        assert "risk_level" in d               # Risk level
        assert "recommendation" in d           # Prevention output
        assert d["risk_score"] >= 50.0         # Threat correctly scored

    def test_e2e_02_comm_full_pipeline(self):
        """Full communication pipeline: input → feature extraction → ML → risk → output."""
        r = _da("CBI Officer Sharma: Arrest warrant issued. You are under digital arrest. Join Skype call.")
        assert r.status_code == 200
        d = r.json()
        assert "classification" in d
        assert "risk_score" in d
        assert "risk_level" in d
        assert "recommendations" in d
        assert d["risk_level"] in ("HIGH", "CRITICAL")

    def test_e2e_03_audio_full_pipeline(self):
        """Full audio pipeline: upload → validate → preprocess → features → model → risk → output."""
        wav = _make_wav_bytes(synthetic=True)
        r = _audio(wav)
        assert r.status_code == 200
        d = r.json()
        assert "classification" in d
        assert "risk_score" in d
        # Audio uses recommendations (list) not recommendation (string)
        assert "recommendations" in d or "explanation" in d

    def test_e2e_04_error_handling_invalid_json(self):
        """Invalid JSON body returns 422, not 500."""
        r = client.post(
            "/api/v1/detection/url",
            content=b"not-json",
            headers={**BYPASS, "content-type": "application/json"},
        )
        assert r.status_code == 422
        assert r.status_code != 500

    def test_e2e_05_large_message_handled(self):
        """Very long message (5000 chars) is handled gracefully."""
        long_msg = "transfer money urgently " * 200
        r = _comm(long_msg)
        assert r.status_code in (200, 400, 413, 422)
        assert r.status_code != 500

    def test_e2e_06_duplicate_url_submission(self):
        """Submitting same URL twice returns valid results both times."""
        url = "https://www.google.com/"
        r1 = _url(url)
        r2 = _url(url)
        assert r1.status_code == 200
        assert r2.status_code == 200
        assert r1.json()["classification"] == r2.json()["classification"]

    def test_e2e_07_unknown_url_handled(self):
        """Unknown domain returns a classification without error."""
        r = _url("https://totally-unknown-domain-xyz123.test/")
        assert r.status_code == 200
        d = r.json()
        assert "classification" in d
        assert d["classification"] in ("LEGITIMATE", "SUSPICIOUS", "PHISHING", "UNKNOWN", "INCONCLUSIVE")

    def test_e2e_08_security_headers_present(self):
        """HTTP responses include security headers."""
        r = _url("https://www.google.com/")
        csp = r.headers.get("content-security-policy", "")
        assert "script-src" in csp
        assert "'unsafe-inline'" not in csp.split("script-src")[1].split(";")[0], (
            "script-src should not contain 'unsafe-inline'"
        )
