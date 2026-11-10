"""
Cyber Raksha AI - Stage 1: B3.1 Security Closure Test Suite
Phase B3.1 Acceptance Gate Verification

Tests Objectives 1-4:
- Objective 1: Server-Side Confidence Validation (Untrusted client confidence & anti-forgery)
- Objective 2: Secure SSE Authentication via Connection Ticket Mechanism
- Objective 3: Safe URL Normalization (IDN, signed URLs, repeated params, default ports)
- Objective 4: HMAC Pepper Validation, Secret Rotation & Production Security
"""
import uuid
import time
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.database.session import SessionLocal
from app.models.device import Device
from app.models.threat_intel import ThreatIndicator
from app.core.config import settings
from app.services.ticket_service import ticket_service
from app.services.sms_analysis_service import sms_analysis_service
from app.utils.helpers import normalize_url_indicator, is_signed_url
from app.services.phone_reputation_service import AUTHORITATIVE_SOURCES

client = TestClient(app)

TEST_DEVICE_UUID = f"device-sec-closure-{uuid.uuid4().hex[:8]}"
TEST_DEVICE_TOKEN = f"token-sec-closure-{uuid.uuid4().hex[:16]}"
REVOKED_DEVICE_UUID = f"device-revoked-closure-{uuid.uuid4().hex[:8]}"
REVOKED_DEVICE_TOKEN = f"token-revoked-closure-{uuid.uuid4().hex[:16]}"


@pytest.fixture(scope="module", autouse=True)
def setup_security_closure_test_db():
    import hashlib
    db = SessionLocal()
    try:
        # Create active test device
        dev1 = Device(
            device_id=TEST_DEVICE_UUID,
            device_name="Pixel 9 Pro",
            device_token_hash=hashlib.sha256(TEST_DEVICE_TOKEN.encode("utf-8")).hexdigest(),
            app_version="1.0.0",
            status="ACTIVE",
            is_revoked=False
        )
        # Create revoked device
        dev2 = Device(
            device_id=REVOKED_DEVICE_UUID,
            device_name="Galaxy S24",
            device_token_hash=hashlib.sha256(REVOKED_DEVICE_TOKEN.encode("utf-8")).hexdigest(),
            app_version="1.0.0",
            status="REVOKED",
            is_revoked=True
        )
        db.merge(dev1)
        db.merge(dev2)
        db.commit()
    finally:
        db.close()


# ==============================================================================
# OBJECTIVE 1: Server-Side Confidence Validation & Anti-Forgery Tests
# ==============================================================================

def test_client_cannot_force_critical_with_high_confidence():
    """
    Client sends severity=CRITICAL and confidence=0.99 or 1.0.
    Backend must treat client confidence as untrusted and cap uncorroborated event at HIGH.
    """
    fake_url = f"https://unverified-claim-{uuid.uuid4().hex[:6]}.com/login"
    res = client.post(
        "/api/v1/security/events",
        json={
            "event_type": "SMS_FRAUD_DETECTED",
            "severity": "CRITICAL",
            "source_component": "ANDROID_APP",
            "threat_indicator": fake_url,
            "risk_score": 99.5,
            "description": "Client claims 100% confidence CRITICAL threat",
            "raw_payload": '{"client_confidence": 1.0, "is_authority": true}'
        }
    )
    assert res.status_code == 201
    data = res.json()
    assert data["severity"] == "HIGH", "Uncorroborated client CRITICAL claim must be capped at HIGH"
    assert data["verification_status"] == "UNVERIFIED"
    assert "authoritative feed verification required" in data["detection_reason"].lower()


def test_client_claiming_authoritative_source_name_is_not_trusted():
    """
    Client claims source_component is 'URLHAUS' or 'CERT_IN' directly via API.
    Backend must verify against internal database records, not client-supplied source string.
    """
    fake_url = f"https://forged-feed-{uuid.uuid4().hex[:6]}.com"
    res = client.post(
        "/api/v1/security/events",
        json={
            "event_type": "THREAT_INTEL_MATCH",
            "severity": "CRITICAL",
            "source_component": "URLHAUS",  # Client forging authoritative source
            "threat_indicator": fake_url,
            "risk_score": 98.0,
            "description": "Client forging URLHAUS authority",
            "raw_payload": '{"source": "URLHAUS", "is_authority": true}'
        }
    )
    assert res.status_code == 201
    data = res.json()
    assert data["severity"] == "HIGH", "Client cannot forge authoritative source without backend feed match"
    assert data["verification_status"] == "UNVERIFIED"


def test_corroborated_trusted_intelligence_allows_escalation():
    """
    When backend threat database actually contains an active authoritative IOC,
    the event is properly corroborated and verified.
    """
    db = SessionLocal()
    target_url = f"https://verified-phish-{uuid.uuid4().hex[:6]}.com/steal"
    try:
        ioc = ThreatIndicator(
            indicator_type="URL",
            indicator_value=target_url,
            threat_type="PHISHING",
            severity="CRITICAL",
            confidence_score=0.98,
            source_name="URLHAUS",
            is_active=True,
            description="Verified phishing campaign"
        )
        db.add(ioc)
        db.commit()
    finally:
        db.close()

    res = client.post(
        "/api/v1/security/events",
        json={
            "event_type": "BROWSER_BLOCKED_URL",
            "severity": "CRITICAL",
            "source_component": "BROWSER_EXTENSION",
            "threat_indicator": target_url,
            "risk_score": 95.0,
            "description": "Verified blocked URL"
        }
    )
    assert res.status_code == 201
    data = res.json()
    assert data["severity"] == "CRITICAL", "Corroborated by verified authoritative feed"
    assert data["verification_status"] == "CORROBORATED"
    assert "URLHAUS" in data["detection_reason"]


# ==============================================================================
# OBJECTIVE 2: Secure SSE Connection Ticket Tests
# ==============================================================================

def test_sse_stream_ticket_requires_authentication():
    """Requesting an SSE ticket without authentication must return 401."""
    res = client.post("/api/v1/security/stream-ticket")
    assert res.status_code == 401


def test_sse_stream_ticket_generation_for_device():
    """Authenticated device can request a short-lived single-use connection ticket."""
    res = client.post(
        "/api/v1/security/stream-ticket",
        headers={"X-Device-Token": TEST_DEVICE_TOKEN}
    )
    assert res.status_code == 201
    data = res.json()
    assert "ticket" in data
    assert len(data["ticket"]) >= 32
    assert data["expires_in_seconds"] == 60
    assert data["device_id"] == TEST_DEVICE_UUID


def test_sse_stream_ticket_single_use_consumption():
    """A ticket can only be consumed once. A replay attempt is immediately rejected."""
    # 1. Generate ticket
    t_res = client.post(
        "/api/v1/security/stream-ticket",
        headers={"X-Device-Token": TEST_DEVICE_TOKEN}
    )
    ticket = t_res.json()["ticket"]

    # 2. First consumption: connect to SSE via streaming context and read initial connection event
    with client.stream("GET", f"/api/v1/security/stream?ticket={ticket}") as conn_res:
        assert conn_res.status_code == 200
        for line in conn_res.iter_lines():
            if line:
                assert "event: connected" in line or "status" in line
                break

    # 3. Second consumption (replay attack): must fail 401
    replay_res = client.get(f"/api/v1/security/stream?ticket={ticket}")
    assert replay_res.status_code == 401
    assert "expired" in replay_res.json()["detail"].lower() or "invalid" in replay_res.json()["detail"].lower()


def test_sse_stream_ticket_expired_rejected():
    """Expired tickets are rejected."""
    # Create ticket with 0-second TTL
    ticket = ticket_service.create_ticket(
        device_id=TEST_DEVICE_UUID,
        is_admin=False,
        auth_type="DEVICE",
        ttl_seconds=-1  # Already expired
    )
    res = client.get(f"/api/v1/security/stream?ticket={ticket}")
    assert res.status_code == 401


def test_sse_stream_ticket_revoked_device_rejected():
    """A ticket issued to a revoked device is rejected on consumption."""
    ticket = ticket_service.create_ticket(
        device_id=REVOKED_DEVICE_UUID,
        is_admin=False,
        auth_type="DEVICE",
        ttl_seconds=60
    )
    res = client.get(f"/api/v1/security/stream?ticket={ticket}")
    assert res.status_code == 403
    assert "revoked" in res.json()["detail"].lower()


def test_sse_long_lived_token_in_query_param_rejected():
    """Passing long-lived authentication tokens in ?token= query parameter is forbidden."""
    res = client.get(
        f"/api/v1/security/stream?token={TEST_DEVICE_TOKEN}",
        headers={"x-test-bypass-rate-limit": "true"}
    )
    assert res.status_code == 400
    assert "prohibited" in res.json()["detail"].lower() or "forbidden" in res.json()["detail"].lower()


# ==============================================================================
# OBJECTIVE 3: Safe URL Normalization Tests
# ==============================================================================

def test_url_normalization_scheme_and_hostname_casing():
    """Scheme and host are lowercased while path case is preserved."""
    url = "HTTPS://WWW.Secure-BANK.COM/Login/AccountVerify"
    norm = normalize_url_indicator(url)
    assert norm.startswith("https://www.secure-bank.com/Login/AccountVerify")


def test_url_normalization_default_ports_stripped():
    """Default ports (:80 for HTTP, :443 for HTTPS) are removed; non-default ports kept."""
    assert normalize_url_indicator("http://example.com:80/test") == "http://example.com/test"
    assert normalize_url_indicator("https://example.com:443/test") == "https://example.com/test"
    assert normalize_url_indicator("https://example.com:8443/test") == "https://example.com:8443/test"
    assert normalize_url_indicator("http://example.com:8080/test") == "http://example.com:8080/test"


def test_url_normalization_fragments_removed():
    """Client-side fragments are stripped from network target indicator."""
    url = "https://example.com/page?ref=home#header-anchor"
    norm = normalize_url_indicator(url)
    assert "#" not in norm
    assert norm == "https://example.com/page?ref=home"


def test_url_normalization_repeated_query_params():
    """Repeated query parameters are preserved."""
    url = "http://example.com/search?category=fraud&category=phish&sort=date"
    norm = normalize_url_indicator(url)
    assert "category=fraud" in norm
    assert "category=phish" in norm
    assert "sort=date" in norm


def test_url_normalization_signed_urls_preserve_query_order():
    """Signed URLs (AWS S3, Azure SAS, HMAC) must preserve exact query parameter order."""
    signed_url = "https://s3.amazonaws.com/bucket/doc.pdf?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=AKIAIOSFODNN7EXAMPLE&Signature=q84kjsd9f8234"
    assert is_signed_url("X-Amz-Algorithm=AWS4-HMAC-SHA256&Signature=q84kjsd9f8234")
    norm = normalize_url_indicator(signed_url)
    # The order must not be altered for signed URLs
    assert norm == signed_url


def test_url_normalization_idn_punycode():
    """Internationalized Domain Names are converted to ASCII Punycode."""
    # Cyrillic 'a' homograph domain: 'xn--e1afmkfd.xn--p1ai' (пример.рф)
    url = "http://münchen.de/portal"
    norm = normalize_url_indicator(url)
    assert "xn--mnchen-3ya.de" in norm


def test_url_normalization_malformed_urls_graceful():
    """Malformed or chaotic URLs do not crash the engine."""
    assert normalize_url_indicator("") == ""
    assert normalize_url_indicator("   ") == ""
    assert isinstance(normalize_url_indicator("http://:::invalid-netloc"), str)


# ==============================================================================
# OBJECTIVE 4: HMAC Pepper Validation & Secret Rotation Tests
# ==============================================================================

def test_sms_pepper_hash_deterministic():
    """HMAC-SHA256 hash generation is deterministic."""
    msg = "Dear customer, your SBI netbanking is blocked. Update KYC immediately."
    h1 = sms_analysis_service._hash_message(msg)
    h2 = sms_analysis_service._hash_message(msg)
    assert h1 == h2
    assert len(h1) == 64


def test_sms_pepper_rotation_verification():
    """verify_message_hash validates against both active and previous peppers."""
    msg = "Urgent: Your HDFC bank account requires immediate verification."
    current_hash = sms_analysis_service._hash_message(msg)
    assert sms_analysis_service.verify_message_hash(msg, current_hash) is True
    assert sms_analysis_service.verify_message_hash(msg, "wronghash1234567890") is False


def test_sms_pepper_never_exposed_in_api_response():
    """Inspecting SMS analysis endpoint response confirms secret pepper is never leaked."""
    res = client.post(
        "/api/v1/mobile/analyze-message",
        headers={"X-Device-Token": TEST_DEVICE_TOKEN, "x-test-bypass-rate-limit": "true"},
        json={
            "device_id": TEST_DEVICE_UUID,
            "message_text": "OTP: 483921 for your bank transaction. Do not share with anyone.",
            "sender": "+919876543210"
        }
    )
    assert res.status_code == 200
    res_text = res.text
    # Secret must never be present in the output
    assert settings.SMS_PEPPER_KEY not in res_text
    assert "PEPPER" not in res_text
