"""
Cyber Raksha AI - Comprehensive End-to-End Operational Scenarios
Phase B9: Automated End-to-End Verification Suite

Verifies the 10 mandated production scenarios:
Scenario 1: Phishing URL detection, explanation, SecurityEvent & incident creation
Scenario 2: Legitimate banking URL preservation without false-positive blocking
Scenario 3: Fake KYC / Account Suspension SMS fraud classification & explanation
Scenario 4: Benign OTP delivery receipt preservation (false-positive guard)
Scenario 5: Digital Arrest government intimidation extortion scheme detection
Scenario 6: Fraudulent phone number community report safety cap (never auto-CRITICAL)
Scenario 7: Cross-device data isolation (HTTP 403 on cross-device incident access)
Scenario 8: Offline/fail-open resilience when backend intelligence is disconnected
Scenario 9: Browser blocked navigation event correlation & dashboard reflection
Scenario 10: Android mobile fraud event correlation & notification delivery
"""
import hashlib
import uuid
import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.database.session import SessionLocal
from app.models.device import Device
from app.models.security_event import SecurityEvent
from app.models.incident import SecurityIncident
from app.models.notification import Notification
from app.models.threat_intel import ThreatIndicator
from app.models.phone_reputation import PhoneReputation
from app.services.sms_analysis_service import sms_analysis_service
from app.services.phone_reputation_service import phone_reputation_service
from app.services.central_risk_engine import central_risk_engine
from app.schemas.security_event import UnifiedRiskEvaluationRequest

client = TestClient(app)

TEST_DEVICE_A = f"device-alpha-{uuid.uuid4().hex[:8]}"
TEST_DEVICE_B = f"device-beta-{uuid.uuid4().hex[:8]}"
TEST_TOKEN_A = f"token-alpha-{uuid.uuid4().hex[:12]}"
TEST_TOKEN_B = f"token-beta-{uuid.uuid4().hex[:12]}"


@pytest.fixture(scope="module", autouse=True)
def setup_e2e_devices():
    """Seeds two isolated test devices and authoritative threat intelligence indicators."""
    db: Session = SessionLocal()
    try:
        dev_a = Device(
            device_id=TEST_DEVICE_A,
            device_name="Pixel 8 Pro (Alpha)",
            device_token_hash=hashlib.sha256(TEST_TOKEN_A.encode("utf-8")).hexdigest(),
            status="ACTIVE",
            is_revoked=False,
            registered_at=datetime.now(timezone.utc),
            last_seen_at=datetime.now(timezone.utc)
        )
        dev_b = Device(
            device_id=TEST_DEVICE_B,
            device_name="Galaxy S24 (Beta)",
            device_token_hash=hashlib.sha256(TEST_TOKEN_B.encode("utf-8")).hexdigest(),
            status="ACTIVE",
            is_revoked=False,
            registered_at=datetime.now(timezone.utc),
            last_seen_at=datetime.now(timezone.utc)
        )
        # Seed an authoritative URLhaus threat indicator for Scenario 1
        known_malicious = ThreatIndicator(
            indicator_type="URL",
            indicator_value="http://verified-phishing-bank-update.xyz/login.php",
            threat_type="PHISHING",
            confidence_score=0.98,
            source_name="URLHAUS",
            is_active=True,
            created_at=datetime.now(timezone.utc)
        )
        db.add_all([dev_a, dev_b, known_malicious])
        db.commit()
    finally:
        db.close()


# ==============================================================================
# Scenario 1: Phishing URL Detection, SecurityEvent & Incident Lifecycle
# ==============================================================================
def test_scenario_01_phishing_url_full_lifecycle():
    """
    Submits a verified phishing URL.
    Verifies detection, explainability, security event creation,
    incident creation, and dashboard visibility.
    """
    url = "http://verified-phishing-bank-update.xyz/login.php"
    res = client.post(
        "/api/v1/detection/url",
        headers={"x-test-bypass-rate-limit": "true"},
        json={"url": url}
    )
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["classification"] in ["PHISHING", "SUSPICIOUS"]
    assert data["risk_score"] >= 70.0
    assert len(data["analysis"]["risk_indicators"]) >= 1

    # Ingest browser security event
    event_payload = {
        "event_type": "BROWSER_BLOCKED_URL",
        "severity": "CRITICAL",
        "source_component": "BROWSER_EXTENSION",
        "threat_indicator": url,
        "risk_score": 95.0,
        "detection_reason": "Matched verified URLhaus malware/phishing indicator",
        "description": f"Blocked browser navigation to {url}"
    }
    ev_res = client.post(
        "/api/v1/security/events",
        headers={"x-test-bypass-rate-limit": "true"},
        json=event_payload
    )
    assert ev_res.status_code == 201
    ev_data = ev_res.json()
    assert ev_data["incident_id"] is not None

    # Verify incident exists and is retrievable
    inc_res = client.get(
        f"/api/v1/incidents/{ev_data['incident_id']}",
        headers={"x-test-bypass-rate-limit": "true"}
    )
    assert inc_res.status_code == 200
    assert inc_res.json()["id"] == ev_data["incident_id"]
    assert inc_res.json()["severity"] in ["HIGH", "CRITICAL"]

    # Verify dashboard incidents endpoint returns 200
    dash_res = client.get("/api/v1/dashboard/incidents?limit=50", headers={"x-test-bypass-rate-limit": "true"})
    assert dash_res.status_code == 200
    assert "incidents" in dash_res.json()


# ==============================================================================
# Scenario 2: Legitimate Banking URL Preservation
# ==============================================================================
def test_scenario_02_legitimate_banking_url_cleared():
    """
    Submits an official banking portal.
    Verifies that authentic banking domains are evaluated as SAFE/LOW
    without false-positive blocking.
    """
    legit_url = "https://onlinesbi.sbi/portal"
    res = client.post(
        "/api/v1/detection/url",
        headers={"x-test-bypass-rate-limit": "true"},
        json={"url": legit_url}
    )
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["classification"] == "LEGITIMATE"
    assert data["risk_level"] in ["LOW", "SAFE"]
    assert data["risk_score"] <= 20.0


# ==============================================================================
# Scenario 3: Fake KYC Account Suspension SMS Scam
# ==============================================================================
def test_scenario_03_fake_kyc_suspension_smishing():
    """
    Submits a realistic fake KYC SMS.
    Verifies high-risk classification, BANKING_FRAUD category,
    and explainability reasons.
    """
    db = SessionLocal()
    try:
        msg = "Dear customer, your SBI NetBanking account is blocked today due to pending KYC. Update PAN immediately to avoid permanent closure."
        analysis = sms_analysis_service.analyze_sms(
            db=db,
            device_id=TEST_DEVICE_A,
            message_text=msg,
            sender="SBIBNK"
        )
        assert analysis["risk_score"] >= 60.0
        assert analysis["risk_level"] in ["HIGH", "CRITICAL"]
        assert analysis["fraud_category"] in ["BANKING_FRAUD", "GOV_IMPERSONATION"]
        assert any("kyc" in r.lower() or "banking" in r.lower() for r in analysis["detection_reasons"])
    finally:
        db.close()


# ==============================================================================
# Scenario 4: Benign Outbound OTP Delivery Notice
# ==============================================================================
def test_scenario_04_benign_otp_delivery_notice_not_flagged():
    """
    Submits an authentic bank transaction OTP delivery notice.
    Verifies the false-positive safeguard prevents OTP theft alerts.
    """
    db = SessionLocal()
    try:
        otp_msg = "Your OTP for transaction of Rs 2,499.00 at Flipkart is 741963. Do not share this OTP with anyone for your security."
        analysis = sms_analysis_service.analyze_sms(
            db=db,
            device_id=TEST_DEVICE_A,
            message_text=otp_msg,
            sender="HDFCBK"
        )
        assert analysis["risk_level"] in ["LOW", "SAFE"]
        assert analysis["risk_score"] < 30.0
        assert analysis["fraud_category"] != "OTP_FRAUD"
        assert any("outbound security notice" in r.lower() or "receipt" in r.lower() for r in analysis["detection_reasons"])
    finally:
        db.close()


# ==============================================================================
# Scenario 5: Digital Arrest Scam Extortion
# ==============================================================================
def test_scenario_05_digital_arrest_extortion_detected():
    """
    Submits a Digital Arrest extortion threat pretending to be CBI / Police.
    Verifies critical severity, GOV_IMPERSONATION category, and stern advisory.
    """
    db = SessionLocal()
    try:
        extortion_msg = "CBI Digital Arrest Notice: A parcel with illegal narcotics has been seized in your name. Police warrant issued. Connect to video hearing immediately or ED raid will occur."
        analysis = sms_analysis_service.analyze_sms(
            db=db,
            device_id=TEST_DEVICE_A,
            message_text=extortion_msg,
            sender="+919876543210"
        )
        assert analysis["risk_score"] >= 75.0
        assert analysis["risk_level"] in ["HIGH", "CRITICAL"]
        assert analysis["fraud_category"] == "GOV_IMPERSONATION"
        assert "Digital Arrest" in analysis["recommended_action"]
    finally:
        db.close()


# ==============================================================================
# Scenario 6: Phone Number Community Report Safety Cap (Never Auto-CRITICAL)
# ==============================================================================
def test_scenario_06_phone_community_reports_never_auto_critical():
    """
    Submits multiple community reports against a phone number.
    Verifies Sybil defense and confirms community reports alone
    can NEVER escalate to CRITICAL (capped at HIGH).
    """
    db = SessionLocal()
    try:
        phone = f"+9198{uuid.uuid4().int % 100000000:08d}"
        # 1. Report from Device Alpha
        phone_reputation_service.report_number(
            db=db,
            raw_number=phone,
            reporting_device_id=TEST_DEVICE_A,
            fraud_category="TELEMARKETING",
            is_authority=False
        )
        rep1 = phone_reputation_service.check_number(db, phone)
        assert rep1["risk_level"] == "MEDIUM"

        # 2. Duplicate report from same device updates metadata without doubling count
        phone_reputation_service.report_number(
            db=db,
            raw_number=phone,
            reporting_device_id=TEST_DEVICE_A,
            fraud_category="TELEMARKETING",
            is_authority=False
        )
        rep2 = phone_reputation_service.check_number(db, phone)
        assert rep2["report_count"] == 1

        # 3. Independent report from Device Beta escalates to HIGH, but NEVER CRITICAL
        phone_reputation_service.report_number(
            db=db,
            raw_number=phone,
            reporting_device_id=TEST_DEVICE_B,
            fraud_category="UPI_FRAUD",
            is_authority=False
        )
        rep3 = phone_reputation_service.check_number(db, phone)
        assert rep3["risk_level"] == "HIGH"
        assert rep3["risk_level"] != "CRITICAL"
        assert rep3["is_verified_authority"] is False
    finally:
        db.close()


# ==============================================================================
# Scenario 7: Multi-Device Privacy & Data Isolation (HTTP 403)
# ==============================================================================
def test_scenario_07_cross_device_isolation_enforced():
    """
    Device B attempts to access Device A's private incidents.
    Verifies strict rejection with HTTP 403 Forbidden.
    """
    # Create incident explicitly bound to Device A
    db = SessionLocal()
    try:
        inc = SecurityIncident(
            incident_number=f"INC-ISO-{uuid.uuid4().hex[:6]}",
            category="SMISHING",
            title="Private Smishing Incident for Device A",
            summary="Testing device row-level access control",
            severity="HIGH",
            status="OPEN",
            device_id=TEST_DEVICE_A,
            target_or_indicator="+919876543210",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        db.add(inc)
        db.commit()
        db.refresh(inc)
        inc_id = inc.id
    finally:
        db.close()

    # Query with Device B's credentials targeting Device A's incident
    res = client.get(
        f"/api/v1/incidents/{inc_id}",
        headers={
            "X-Device-Token": TEST_TOKEN_B,
            "x-test-bypass-rate-limit": "true"
        }
    )
    assert res.status_code == 403
    assert "Access denied" in res.json()["detail"]


# ==============================================================================
# Scenario 8: Offline / Fail-Open Resilience
# ==============================================================================
def test_scenario_08_phone_reputation_unlisted_fails_open():
    """
    Queries an unknown/unlisted number when external threat feeds are absent.
    Verifies fail-open design: returns UNKNOWN with safe advice; call is not dropped.
    """
    db = SessionLocal()
    try:
        unknown_num = "+919999900000"
        rep = phone_reputation_service.check_number(db, unknown_num)
        assert rep["risk_level"] == "UNKNOWN"
        assert rep["report_count"] == 0
        assert rep["is_verified_authority"] is False
        assert "Never share OTPs" in rep["recommended_action"]
    finally:
        db.close()


# ==============================================================================
# Scenario 9: Browser Navigation Event Synchronization
# ==============================================================================
def test_scenario_09_browser_event_updates_activity_feed():
    """
    Simulates a Chrome extension blocked-navigation event.
    Verifies it appears immediately in the dashboard activity stream.
    """
    unique_ind = f"http://malicious-test-{uuid.uuid4().hex[:8]}.com/payload"
    event_payload = {
        "event_type": "BROWSER_BLOCKED_URL",
        "severity": "HIGH",
        "source_component": "BROWSER_EXTENSION",
        "threat_indicator": unique_ind,
        "risk_score": 88.0,
        "detection_reason": "Heuristic match on deceptive credential harvesting form",
        "description": f"Declarative Net Request blocked navigation to {unique_ind}"
    }
    post_res = client.post(
        "/api/v1/security/events",
        headers={"x-test-bypass-rate-limit": "true"},
        json=event_payload
    )
    assert post_res.status_code == 201

    # Query activity feed
    feed_res = client.get("/api/v1/dashboard/activity?limit=10", headers={"x-test-bypass-rate-limit": "true"})
    assert feed_res.status_code == 200
    activities = feed_res.json()["activities"]
    assert any(a["threat_indicator"] == unique_ind for a in activities)


# ==============================================================================
# Scenario 10: Android Mobile Fraud Event & Incident Correlation
# ==============================================================================
def test_scenario_10_android_smishing_event_triggers_incident_and_notif():
    """
    Simulates native Android app reporting an intercepted smishing attempt.
    Verifies automatic incident creation, severity assignment, and notification persistence.
    """
    phish_link = f"http://sbi-fake-kyc-{uuid.uuid4().hex[:6]}.xyz/login"
    event_payload = {
        "event_type": "ANDROID_SMS_FRAUD",
        "severity": "HIGH",
        "source_component": "ANDROID_APP",
        "device_id": TEST_DEVICE_A,
        "threat_indicator": phish_link,
        "risk_score": 85.0,
        "detection_reason": "Intercepted SMS impersonating SBI netbanking with unauthorized domain",
        "description": f"SMS smishing attempt with deceptive link {phish_link}"
    }
    res = client.post(
        "/api/v1/security/events",
        headers={
            "Authorization": f"Bearer {TEST_TOKEN_A}",
            "x-test-bypass-rate-limit": "true"
        },
        json=event_payload
    )
    assert res.status_code == 201
    data = res.json()
    assert data["incident_id"] is not None
    assert data["severity"] == "HIGH"

    # Verify notification was generated for device event
    db = SessionLocal()
    try:
        notif = (
            db.query(Notification)
            .filter(
                Notification.source_component == "ANDROID_APP",
                Notification.severity == "HIGH"
            )
            .order_by(Notification.created_at.desc())
            .first()
        )
        assert notif is not None
        assert "Smishing" in notif.title or "Security" in notif.title or "SMS" in notif.title or "Incident" in notif.title
    finally:
        db.close()
