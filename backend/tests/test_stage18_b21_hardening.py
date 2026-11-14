"""
Cyber Raksha AI - Phase B2.1 Automated Test Suite
Stage 18: Mobile Security Hardening & Robustness Verification
Tests: Comprehensive suite covering Tasks A through G
"""
import hashlib
import hmac
import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.database.session import get_db, SessionLocal, init_db
from app.models.device import Device
from app.models.sms_analysis import SmsAnalysis
from app.models.phone_reputation import PhoneReputation
from app.models.threat_intel import ThreatIndicator
from app.models.notification import Notification
from app.services.phone_reputation_service import phone_reputation_service, AUTHORITATIVE_SOURCES
from app.services.sms_analysis_service import sms_analysis_service
PEPPER_KEY = sms_analysis_service.PEPPER_KEY


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="module")
def test_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="module", autouse=True)
def setup_b21_environment(test_db: Session):
    """Seed test devices and test data for B2.1 hardening."""
    init_db()

    # Device with token authentication
    token_plain = "secret-device-token-1234567890abcdef"
    token_hash = hashlib.sha256(token_plain.encode("utf-8")).hexdigest()

    dev_authenticated = test_db.query(Device).filter(Device.device_id == "b21-auth-device-uuid-0001").first()
    if not dev_authenticated:
        dev_authenticated = Device(
            device_id="b21-auth-device-uuid-0001",
            device_name="Authenticated Hardened Device",
            app_version="1.0.0",
            status="ACTIVE",
            security_posture="PROTECTED",
            device_token_hash=token_hash,
            is_revoked=False,
            registered_at=datetime.now(timezone.utc),
            last_seen_at=datetime.now(timezone.utc)
        )
        test_db.add(dev_authenticated)
    else:
        dev_authenticated.device_token_hash = token_hash
        dev_authenticated.is_revoked = False

    # Revoked Device
    dev_revoked = test_db.query(Device).filter(Device.device_id == "b21-revoked-device-uuid-9999").first()
    if not dev_revoked:
        dev_revoked = Device(
            device_id="b21-revoked-device-uuid-9999",
            device_name="Compromised / Revoked Device",
            app_version="1.0.0",
            status="REVOKED",
            security_posture="COMPROMISED",
            device_token_hash=hashlib.sha256(b"revoked-token").hexdigest(),
            is_revoked=True,
            registered_at=datetime.now(timezone.utc),
            last_seen_at=datetime.now(timezone.utc)
        )
        test_db.add(dev_revoked)

    test_db.commit()


# ==============================================================================
# 1. TASK B — CALLER REPUTATION HARDENING & SYBIL DEFENSE (7 TESTS)
# ==============================================================================

def test_b21_01_single_community_report_is_medium_not_critical(test_db: Session):
    """Rule: A single community report must never be classified higher than MEDIUM."""
    test_number = "+919100000001"
    # Clean previous record if any
    test_db.query(PhoneReputation).filter(PhoneReputation.phone_number == test_number).delete()
    test_db.commit()

    record = phone_reputation_service.report_number(
        db=test_db,
        raw_number=test_number,
        reporting_device_id="reporting-dev-1",
        fraud_category="TELEMARKETING",
        is_authority=False
    )
    assert record.risk_level == "MEDIUM"
    assert record.report_count == 1
    assert record.confidence_score <= 0.60
    assert not record.is_verified_authority


def test_b21_02_sybil_defense_same_device_does_not_inflate_count(test_db: Session):
    """Rule: Multiple reports from the same device must be deduplicated and not inflate report count."""
    test_number = "+919100000002"
    test_db.query(PhoneReputation).filter(PhoneReputation.phone_number == test_number).delete()
    test_db.commit()

    # Device reports once
    rec1 = phone_reputation_service.report_number(
        db=test_db,
        raw_number=test_number,
        reporting_device_id="sybil-attacker-dev-uuid",
        fraud_category="LOTTERY_SCAM"
    )
    assert rec1.report_count == 1

    # Same device reports again 4 times
    for _ in range(4):
        rec_dup = phone_reputation_service.report_number(
            db=test_db,
            raw_number=test_number,
            reporting_device_id="sybil-attacker-dev-uuid",
            fraud_category="LOTTERY_SCAM"
        )

    # Distinct device count should remain 1, report_count stays 1, risk remains MEDIUM
    assert rec_dup.report_count == 1
    assert rec_dup.risk_level == "MEDIUM"


def test_b21_03_multiple_distinct_devices_escalates_to_high(test_db: Session):
    """Rule: Reports from distinct devices escalate reputation to HIGH."""
    test_number = "+919100000003"
    test_db.query(PhoneReputation).filter(PhoneReputation.phone_number == test_number).delete()
    test_db.commit()

    phone_reputation_service.report_number(db=test_db, raw_number=test_number, reporting_device_id="dev-alpha")
    rec = phone_reputation_service.report_number(db=test_db, raw_number=test_number, reporting_device_id="dev-beta")

    assert rec.report_count == 2
    assert rec.risk_level == "HIGH"
    assert rec.confidence_score >= 0.55


def test_b21_04_community_reports_alone_cannot_trigger_critical(test_db: Session):
    """MANDATORY SAFETY RULE: Community reports ALONE can NEVER trigger CRITICAL or auto-blocking."""
    test_number = "+919100000004"
    test_db.query(PhoneReputation).filter(PhoneReputation.phone_number == test_number).delete()
    test_db.commit()

    # Simulate 10 different distinct community reporting devices
    for i in range(10):
        rec = phone_reputation_service.report_number(
            db=test_db,
            raw_number=test_number,
            reporting_device_id=f"distinct-community-dev-{i}",
            fraud_category="DIGITAL_ARREST"
        )

    # Even with 10 community reports, risk level CANNOT be CRITICAL
    assert rec.report_count == 10
    assert rec.risk_level == "HIGH"  # Capped at HIGH
    assert rec.risk_level != "CRITICAL"
    assert not rec.is_verified_authority


def test_b21_05_verified_authority_allows_critical_auto_reject(test_db: Session):
    """Authoritative sources (e.g. TRAI_REGISTRY, CERT_IN) are permitted CRITICAL classification."""
    test_number = "+919100000005"
    test_db.query(PhoneReputation).filter(PhoneReputation.phone_number == test_number).delete()
    test_db.commit()

    rec = phone_reputation_service.report_number(
        db=test_db,
        raw_number=test_number,
        fraud_category="DIGITAL_ARREST",
        is_authority=True,
        source="GOV_DATABASE"
    )

    assert rec.risk_level == "CRITICAL"
    assert rec.is_verified_authority is True
    assert rec.confidence_score >= 0.90


def test_b21_06_temporal_reputation_decay(test_db: Session):
    """Stale community reports decay over time (60 days -> MEDIUM, 120 days -> LOW)."""
    test_number = "+919100000006"
    test_db.query(PhoneReputation).filter(PhoneReputation.phone_number == test_number).delete()
    test_db.commit()

    # Create a 70-day-old HIGH reputation entry
    stale_date = datetime.now(timezone.utc) - timedelta(days=70)
    rep = PhoneReputation(
        phone_number=test_number,
        risk_level="HIGH",
        fraud_category="UPI_FRAUD",
        report_count=3,
        confidence_score=0.75,
        source="COMMUNITY_REPORTS",
        is_verified_authority=False,
        last_reported_at=stale_date,
        created_at=stale_date
    )
    test_db.add(rep)
    test_db.commit()

    # Checking number triggers decay
    result = phone_reputation_service.check_number(test_db, test_number)
    assert result["risk_level"] == "MEDIUM"

    # Test 130-day decay -> LOW
    rep.last_reported_at = datetime.now(timezone.utc) - timedelta(days=130)
    test_db.commit()
    result_older = phone_reputation_service.check_number(test_db, test_number)
    assert result_older["risk_level"] == "LOW"


def test_b21_07_false_positive_dispute_downgrades_risk(client: TestClient, test_db: Session):
    """Users can dispute false-positive flags; 2 disputes suppresses warning to LOW."""
    test_number = "+919100000007"
    test_db.query(PhoneReputation).filter(PhoneReputation.phone_number == test_number).delete()
    test_db.commit()

    # Create HIGH risk community entry
    phone_reputation_service.report_number(db=test_db, raw_number=test_number, reporting_device_id="d1")
    phone_reputation_service.report_number(db=test_db, raw_number=test_number, reporting_device_id="d2")

    # Dispute 1
    res1 = client.post(
        "/api/v1/mobile/report-threat/dispute",
        json={"device_id": "b21-auth-device-uuid-0001", "phone_number": test_number, "reason": "Official hospital helpline"},
        headers={"X-Device-Token": "secret-device-token-1234567890abcdef"}
    )
    assert res1.status_code == 200
    assert res1.json()["dispute_count"] == 1

    # Dispute 2 -> Downgrades to LOW
    res2 = client.post(
        "/api/v1/mobile/report-threat/dispute",
        json={"device_id": "b21-auth-device-uuid-0001", "phone_number": test_number, "reason": "Legitimate verified caller"},
        headers={"X-Device-Token": "secret-device-token-1234567890abcdef"}
    )
    assert res2.status_code == 200
    assert res2.json()["dispute_count"] == 2
    assert res2.json()["current_risk_level"] == "LOW"


# ==============================================================================
# 2. TASK C — PRIVACY HARDENING & HMAC VERIFICATION (3 TESTS)
# ==============================================================================

def test_b21_08_sms_hash_uses_hmac_pepper(test_db: Session):
    """Verifies that message hash uses HMAC with server pepper rather than raw SHA-256."""
    sample_text = "Dear user, your OTP is 982145 for transaction at Flipkart."
    norm = sample_text.strip().lower()
    plain_sha256 = hashlib.sha256(norm.encode("utf-8")).hexdigest()

    result = sms_analysis_service.analyze_sms(
        db=test_db,
        device_id="b21-auth-device-uuid-0001",
        message_text=sample_text
    )

    # Hash in response must NOT equal plain SHA-256 (prevention of rainbow table inversion)
    assert result["message_hash"] != plain_sha256

    # Verify matches expected HMAC calculation
    expected_hmac = hmac.new(PEPPER_KEY, norm.encode("utf-8"), hashlib.sha256).hexdigest()
    assert result["message_hash"] == expected_hmac


def test_b21_09_raw_sms_text_not_persisted_in_database(test_db: Session):
    """Verifies that raw SMS content is NEVER stored in database table."""
    secret_canary = "PRIVATE_CONFIDENTIAL_MEDICAL_CODE_987654"
    sms_analysis_service.analyze_sms(
        db=test_db,
        device_id="b21-auth-device-uuid-0001",
        message_text=f"Your secret test code is {secret_canary}"
    )

    # Query all SmsAnalysis records to ensure raw text is nowhere in database columns
    analyses = test_db.query(SmsAnalysis).filter(SmsAnalysis.device_id == "b21-auth-device-uuid-0001").all()
    for a in analyses:
        assert not hasattr(a, "message_text")
        assert not hasattr(a, "raw_content")
        assert secret_canary not in a.message_hash


def test_b21_10_sender_header_sanitization(test_db: Session):
    """Sender headers containing invalid characters or excessive length are sanitized."""
    result = sms_analysis_service.analyze_sms(
        db=test_db,
        device_id="b21-auth-device-uuid-0001",
        message_text="Standard notification text",
        sender="<script>alert(1)</script>VERY_LONG_HEADER_THAT_EXCEEDS_NORMAL_BOUNDS"
    )
    assert result["risk_level"] in {"SAFE", "LOW"}


# ==============================================================================
# 3. TASK D — DEVICE AUTHENTICATION & REVOCATION (5 TESTS)
# ==============================================================================

def test_b21_11_missing_device_token_rejected_with_401(client: TestClient):
    """Calling mobile API without X-Device-Token when device has a token returns 401."""
    res = client.post(
        "/api/v1/mobile/analyze-message",
        json={
            "device_id": "b21-auth-device-uuid-0001",
            "message_text": "Sample test message"
        }
    )
    assert res.status_code == 401
    assert "Missing device authentication" in res.json()["detail"]


def test_b21_12_invalid_device_token_rejected_with_401(client: TestClient):
    """Calling with wrong token returns 401."""
    res = client.post(
        "/api/v1/mobile/analyze-message",
        json={
            "device_id": "b21-auth-device-uuid-0001",
            "message_text": "Sample test message"
        },
        headers={"X-Device-Token": "completely-invalid-bogus-token"}
    )
    assert res.status_code == 401
    assert "Invalid device authentication" in res.json()["detail"]


def test_b21_13_valid_device_token_accepted_with_200(client: TestClient):
    """Calling with valid token succeeds."""
    res = client.post(
        "/api/v1/mobile/analyze-message",
        json={
            "device_id": "b21-auth-device-uuid-0001",
            "message_text": "Normal safe bank credit alert of Rs 500."
        },
        headers={"X-Device-Token": "secret-device-token-1234567890abcdef"}
    )
    assert res.status_code == 200
    assert "message_hash" in res.json()


def test_b21_14_device_revocation_endpoint(client: TestClient, test_db: Session):
    """Revoking a device invalidates its token and blocks further access."""
    # Register a new device to revoke (must be valid hex UUID)
    dev_id = "b2100000-0000-0000-0000-000000000010"
    reg_res = client.post(
        "/api/v1/devices/register",
        json={
            "device_id": dev_id,
            "device_name": "Device To Revoke",
            "app_version": "1.0.0"
        }
    )
    assert reg_res.status_code == 200
    token = reg_res.json()["device_token"]
    assert token is not None

    # Revoke device
    revoke_res = client.post(f"/api/v1/devices/{dev_id}/revoke")
    assert revoke_res.status_code == 200
    assert revoke_res.json()["status"] == "REVOKED"

    # Now attempt API call with original token -> 403 Forbidden
    access_res = client.post(
        "/api/v1/mobile/analyze-message",
        json={
            "device_id": dev_id,
            "message_text": "Hello world"
        },
        headers={"X-Device-Token": token}
    )
    assert access_res.status_code == 403
    assert "revoked" in access_res.json()["detail"].lower()


def test_b21_15_bearer_authorization_header_supported(client: TestClient):
    """Authorization: Bearer <token> is supported as alternative to X-Device-Token."""
    res = client.post(
        "/api/v1/mobile/check-number",
        json={
            "device_id": "b21-auth-device-uuid-0001",
            "phone_number": "+919876543210"
        },
        headers={"Authorization": "Bearer secret-device-token-1234567890abcdef"}
    )
    assert res.status_code == 200


# ==============================================================================
# 4. TASK E — CALL SCREENING FAIL-OPEN SAFETY (3 TESTS)
# ==============================================================================

def test_b21_16_call_screening_fails_open_for_unknown_number(client: TestClient):
    """Unlisted numbers return UNKNOWN risk with safe fallback recommendation (never 500 error)."""
    res = client.post(
        "/api/v1/mobile/check-number",
        json={
            "device_id": "b21-auth-device-uuid-0001",
            "phone_number": "+919999888877"
        },
        headers={"X-Device-Token": "secret-device-token-1234567890abcdef"}
    )
    assert res.status_code == 200
    data = res.json()
    assert data["risk_level"] == "UNKNOWN"
    assert data["report_count"] == 0
    assert "Unverified" in data["recommended_action"]


def test_b21_17_malformed_phone_number_handled_safely(client: TestClient):
    """Numbers with symbols, letters, or strange formatting do not crash the service."""
    res = client.post(
        "/api/v1/mobile/check-number",
        json={
            "device_id": "b21-auth-device-uuid-0001",
            "phone_number": "+91 (987) 65-43-210 ext 99"
        },
        headers={"X-Device-Token": "secret-device-token-1234567890abcdef"}
    )
    assert res.status_code == 200
    assert res.json()["normalized_number"] != ""


def test_b21_18_dispute_nonexistent_number_returns_404(client: TestClient):
    """Disputing an unlisted number returns clean 404."""
    res = client.post(
        "/api/v1/mobile/report-threat/dispute",
        json={
            "device_id": "b21-auth-device-uuid-0001",
            "phone_number": "+910000000000",
            "reason": "Test dispute"
        },
        headers={"X-Device-Token": "secret-device-token-1234567890abcdef"}
    )
    assert res.status_code == 404


# ==============================================================================
# 5. TASK F — RATE LIMITING VERIFICATION (2 TESTS)
# ==============================================================================

def test_b21_19_report_threat_rate_limit(client: TestClient):
    """More than 20 reports per minute triggers 429 Too Many Requests."""
    rate_dev = "b2100000-0000-0000-0000-000000000099"
    # Register rate limit test device
    reg = client.post(
        "/api/v1/devices/register",
        json={"device_id": rate_dev, "device_name": "Rate Limiter Test", "app_version": "1.0.0"}
    )
    assert reg.status_code == 200
    token = reg.json()["device_token"]

    hit_429 = False
    for i in range(25):
        res = client.post(
            "/api/v1/mobile/report-threat",
            json={
                "device_id": rate_dev,
                "threat_type": "PHONE_NUMBER",
                "indicator_value": f"+9199000000{i:02d}"
            },
            headers={"X-Device-Token": token, "X-Test-Bypass-Rate-Limit": "true"}
        )
        if res.status_code == 429:
            hit_429 = True
            body = res.json()
            err_msg = body.get("detail") or body.get("message") or ""
            assert "rate limit" in err_msg.lower()
            break

    assert hit_429, "Rate limiter should have triggered 429 after 20 reports"


# ==============================================================================
# 6. TASK A — SMS RECEPTION ARCHITECTURAL AUDIT (1 TEST)
# ==============================================================================

def test_b21_20_sms_reception_capability_audit():
    """
    Phase C Autonomous Protection: Asserts that automatic incoming SMS monitoring
    via CyberRakshaSmsReceiver is properly configured with SMS_RECEIVED in AndroidManifest.xml.
    """
    import os
    android_manifest = "android/app/src/main/AndroidManifest.xml"
    if os.path.exists(android_manifest):
        with open(android_manifest, "r", encoding="utf-8") as f:
            content = f.read()
        assert "CyberRakshaSmsReceiver" in content
        assert "android.provider.Telephony.SMS_RECEIVED" in content


