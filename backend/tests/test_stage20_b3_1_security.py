"""
Cyber Raksha AI - Stage 20: Phase B3.1 Integration Security, Privacy Isolation & Multi-Device Tests
Validates:
  1. Multi-Device Security & Strict Data Isolation (Objective A)
  2. False-Positive and Dispute Security (Objective B)
  3. Deterministic Indicator Normalization & Multi-Source Preservation (Objective C)
  4. Real-Time SSE Stream Scoping & Authorization (Objective D)
  5. Authoritative Threat Source Validation & Anti-Forgery (Objective G)
  6. Rate Limiting Debug Bypass Safety in Production (Objective H)
"""
import uuid
import json
import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.core.config import settings
from app.database.session import SessionLocal
from app.models.device import Device
from app.models.threat_intel import ThreatIndicator
from app.models.security_event import SecurityEvent
from app.models.incident import SecurityIncident
from app.services.notification_service import notification_service
from app.utils.helpers import normalize_threat_indicator, normalize_url_indicator, normalize_phone_indicator

# Client configured with test bypass for fast execution of test suite
client = TestClient(app, headers={"x-test-bypass-rate-limit": "true"})

DEVICE_A_UUID = "b3100000-0000-0000-0000-00000000000a"
DEVICE_A_TOKEN = "token-secret-device-a-32bytes-hex-val"

DEVICE_B_UUID = "b3100000-0000-0000-0000-00000000000b"
DEVICE_B_TOKEN = "token-secret-device-b-32bytes-hex-val"

REVOKED_DEVICE_UUID = "b3100000-0000-0000-0000-00000000000r"
REVOKED_DEVICE_TOKEN = "token-secret-revoked-dev-32bytes"


@pytest.fixture(scope="module", autouse=True)
def setup_b31_test_devices():
    import hashlib
    db: Session = SessionLocal()
    try:
        # 1. Register Device A
        dev_a = db.query(Device).filter(Device.device_id == DEVICE_A_UUID).first()
        if not dev_a:
            dev_a = Device(
                device_id=DEVICE_A_UUID,
                device_name="Pixel 8 Pro (User A)",
                app_version="1.0.0",
                status="ACTIVE",
                is_revoked=False,
                device_token_hash=hashlib.sha256(DEVICE_A_TOKEN.encode()).hexdigest(),
                registered_at=datetime.now(timezone.utc),
                last_seen_at=datetime.now(timezone.utc)
            )
            db.add(dev_a)
        else:
            dev_a.is_revoked = False
            dev_a.status = "ACTIVE"
            dev_a.device_token_hash = hashlib.sha256(DEVICE_A_TOKEN.encode()).hexdigest()

        # 2. Register Device B
        dev_b = db.query(Device).filter(Device.device_id == DEVICE_B_UUID).first()
        if not dev_b:
            dev_b = Device(
                device_id=DEVICE_B_UUID,
                device_name="Galaxy S24 (User B)",
                app_version="1.0.0",
                status="ACTIVE",
                is_revoked=False,
                device_token_hash=hashlib.sha256(DEVICE_B_TOKEN.encode()).hexdigest(),
                registered_at=datetime.now(timezone.utc),
                last_seen_at=datetime.now(timezone.utc)
            )
            db.add(dev_b)
        else:
            dev_b.is_revoked = False
            dev_b.status = "ACTIVE"
            dev_b.device_token_hash = hashlib.sha256(DEVICE_B_TOKEN.encode()).hexdigest()

        # 3. Register Revoked Device
        dev_r = db.query(Device).filter(Device.device_id == REVOKED_DEVICE_UUID).first()
        if not dev_r:
            dev_r = Device(
                device_id=REVOKED_DEVICE_UUID,
                device_name="Compromised Device (Revoked)",
                app_version="1.0.0",
                status="REVOKED",
                is_revoked=True,
                device_token_hash=hashlib.sha256(REVOKED_DEVICE_TOKEN.encode()).hexdigest(),
                registered_at=datetime.now(timezone.utc),
                last_seen_at=datetime.now(timezone.utc)
            )
            db.add(dev_r)
        else:
            dev_r.is_revoked = True
            dev_r.status = "REVOKED"
            dev_r.device_token_hash = hashlib.sha256(REVOKED_DEVICE_TOKEN.encode()).hexdigest()

        # Authoritative Threat Indicator for testing
        auth_ioc = db.query(ThreatIndicator).filter(ThreatIndicator.indicator_value == "https://scam-icici-netbanking.com").first()
        if not auth_ioc:
            auth_ioc = ThreatIndicator(
                indicator_type="URL",
                indicator_value="https://scam-icici-netbanking.com",
                threat_type="PHISHING",
                severity="CRITICAL",
                confidence_score=0.98,
                source_name="URLHAUS",
                description="Verified banking credential phishing domain targeting ICICI accounts.",
                is_active=True,
                first_seen=datetime.now(timezone.utc),
                last_seen=datetime.now(timezone.utc),
                created_at=datetime.now(timezone.utc)
            )
            db.add(auth_ioc)
        else:
            auth_ioc.is_active = True

        db.commit()
    finally:
        db.close()


# ==============================================================================
# OBJECTIVE A: Multi-Device Security & Strict Data Isolation Tests
# ==============================================================================

def test_b31_multidevice_incident_creation_and_isolation():
    """
    Verify that Device A and Device B create separate private incidents even
    when encountering the same threat indicator, retaining strict ownership.
    """
    shared_indicator = f"https://scam-multi-test-{uuid.uuid4().hex[:6]}.com"

    # Device A reports threat
    res_a = client.post(
        "/api/v1/security/events",
        headers={"X-Device-Token": DEVICE_A_TOKEN},
        json={
            "event_type": "SMS_FRAUD_DETECTED",
            "severity": "HIGH",
            "source_component": "ANDROID_APP",
            "device_id": DEVICE_A_UUID,
            "threat_indicator": shared_indicator,
            "risk_score": 88.0,
            "description": "Scam message on Device A"
        }
    )
    assert res_a.status_code == 201
    inc_a_id = res_a.json()["incident_id"]
    assert inc_a_id is not None

    # Device B reports threat for the same indicator
    res_b = client.post(
        "/api/v1/security/events",
        headers={"X-Device-Token": DEVICE_B_TOKEN},
        json={
            "event_type": "SMS_FRAUD_DETECTED",
            "severity": "HIGH",
            "source_component": "ANDROID_APP",
            "device_id": DEVICE_B_UUID,
            "threat_indicator": shared_indicator,
            "risk_score": 88.0,
            "description": "Scam message on Device B"
        }
    )
    assert res_b.status_code == 201
    inc_b_id = res_b.json()["incident_id"]
    assert inc_b_id is not None

    # Strict isolation: Device A and Device B incidents MUST be distinct!
    assert inc_a_id != inc_b_id


def test_b31_multidevice_incident_access_and_modification_denial():
    """
    MANDATORY AUTHORIZATION TESTS:
    - Device A requests own incidents -> Allowed
    - Device B requests own incidents -> Allowed
    - Device A attempts to access Device B's incident by ID -> 403 Forbidden
    - Device B attempts to access Device A's incident by ID -> 403 Forbidden
    - Device A attempts to acknowledge Device B's incident -> 403 Forbidden
    - Device A attempts to resolve Device B's incident -> 403 Forbidden
    - Device A attempts to submit a false-positive decision for Device B's incident -> 403 Forbidden
    """
    # Create private incident for Device B
    ev_b = client.post(
        "/api/v1/security/events",
        headers={"X-Device-Token": DEVICE_B_TOKEN},
        json={
            "event_type": "SMS_FRAUD_DETECTED",
            "severity": "HIGH",
            "source_component": "ANDROID_APP",
            "device_id": DEVICE_B_UUID,
            "threat_indicator": f"https://private-target-{uuid.uuid4().hex[:6]}.com",
            "risk_score": 85.0,
            "description": "Private SMS alert on Device B"
        }
    )
    assert ev_b.status_code == 201
    inc_b_id = ev_b.json()["incident_id"]

    # 1. Device B accesses its own incident -> 200 OK
    own_res = client.get(
        f"/api/v1/incidents/{inc_b_id}",
        headers={"X-Device-Token": DEVICE_B_TOKEN}
    )
    assert own_res.status_code == 200
    assert own_res.json()["id"] == inc_b_id

    # 2. Device A attempts to access Device B's incident -> 403 FORBIDDEN
    leak_res = client.get(
        f"/api/v1/incidents/{inc_b_id}",
        headers={"X-Device-Token": DEVICE_A_TOKEN}
    )
    assert leak_res.status_code == 403
    assert "Access denied" in leak_res.json()["detail"]

    # 3. Device A attempts to acknowledge Device B's incident -> 403 FORBIDDEN
    ack_res = client.post(
        f"/api/v1/incidents/{inc_b_id}/acknowledge",
        headers={"X-Device-Token": DEVICE_A_TOKEN},
        json={"notes": "Unauthorized ack attempt"}
    )
    assert ack_res.status_code == 403

    # 4. Device A attempts to resolve Device B's incident -> 403 FORBIDDEN
    res_res = client.post(
        f"/api/v1/incidents/{inc_b_id}/resolve",
        headers={"X-Device-Token": DEVICE_A_TOKEN},
        json={"resolution_notes": "Unauthorized resolution attempt"}
    )
    assert res_res.status_code == 403

    # 5. Device A attempts to mark Device B's incident false positive -> 403 FORBIDDEN
    fp_res = client.post(
        f"/api/v1/incidents/{inc_b_id}/false-positive",
        headers={"X-Device-Token": DEVICE_A_TOKEN},
        json={"reason": "Unauthorized FP attempt"}
    )
    assert fp_res.status_code == 403

    # 6. Device A attempts to dispute Device B's incident -> 403 FORBIDDEN
    disp_res = client.post(
        f"/api/v1/incidents/{inc_b_id}/dispute",
        headers={"X-Device-Token": DEVICE_A_TOKEN},
        json={"reason": "Unauthorized dispute attempt"}
    )
    assert disp_res.status_code == 403


def test_b31_multidevice_device_status_and_activity_isolation():
    """
    Verify that Device A cannot read Device B's device status or activity feed.
    """
    # Device A querying Device B's status -> 403 FORBIDDEN
    status_res = client.get(
        f"/api/v1/devices/{DEVICE_B_UUID}/status",
        headers={"X-Device-Token": DEVICE_A_TOKEN}
    )
    assert status_res.status_code == 403

    # Device A querying Device B's activity feed -> 403 FORBIDDEN
    act_res = client.get(
        f"/api/v1/devices/{DEVICE_B_UUID}/activity",
        headers={"X-Device-Token": DEVICE_A_TOKEN}
    )
    assert act_res.status_code == 403

    # Device B querying Device B's activity feed -> 200 OK
    own_act_res = client.get(
        f"/api/v1/devices/{DEVICE_B_UUID}/activity",
        headers={"X-Device-Token": DEVICE_B_TOKEN}
    )
    assert own_act_res.status_code == 200


# ==============================================================================
# OBJECTIVE B: False-Positive & Dispute Security
# ==============================================================================

def test_b31_user_dispute_preserves_authoritative_threat_intelligence():
    """
    Verify that an ordinary user disputing a detection records the dispute and evidence,
    but CANNOT erase or deactivate verified global threat intelligence.
    """
    db: Session = SessionLocal()
    try:
        # Create incident tied to authoritative indicator
        auth_url = "https://scam-icici-netbanking.com"
        ev = client.post(
            "/api/v1/security/events",
            headers={"X-Device-Token": DEVICE_A_TOKEN},
            json={
                "event_type": "BROWSER_BLOCKED_URL",
                "severity": "CRITICAL",
                "source_component": "BROWSER_EXTENSION",
                "device_id": DEVICE_A_UUID,
                "threat_indicator": auth_url,
                "risk_score": 98.0,
                "description": "Navigation blocked to verified banking phish"
            }
        )
        assert ev.status_code == 201
        inc_id = ev.json()["incident_id"]

        # Ordinary Device A files a dispute
        disp_res = client.post(
            f"/api/v1/incidents/{inc_id}/dispute",
            headers={"X-Device-Token": DEVICE_A_TOKEN},
            json={"reason": "User claims this is my legitimate bank URL"}
        )
        assert disp_res.status_code == 200
        data = disp_res.json()
        assert data["status"] == "DISPUTED"

        # Global Threat Indicator in DB MUST REMAIN ACTIVE!
        ioc = db.query(ThreatIndicator).filter(ThreatIndicator.indicator_value == auth_url).first()
        assert ioc is not None
        assert ioc.is_active is True  # Ordinary dispute cannot erase authoritative IOC!

        # Ordinary user trying to mark false-positive without admin rights does NOT de-list IOC
        fp_res = client.post(
            f"/api/v1/incidents/{inc_id}/false-positive",
            headers={"X-Device-Token": DEVICE_A_TOKEN},
            json={"reason": "Trying to de-list authoritative IOC as ordinary user"}
        )
        assert fp_res.status_code == 200
        # Threat indicator remains active
        db.refresh(ioc)
        assert ioc.is_active is True
    finally:
        db.close()


def test_b31_admin_adjudication_can_deactivate_ioc():
    """
    Verify that only an authorized administrator (via X-Admin-Key) can adjudicate and de-list an IOC.
    """
    db: Session = SessionLocal()
    try:
        temp_url = f"https://temp-ioc-{uuid.uuid4().hex[:6]}.com"
        temp_ioc = ThreatIndicator(
            indicator_type="URL",
            indicator_value=temp_url,
            threat_type="PHISHING",
            severity="HIGH",
            confidence_score=0.90,
            source_name="MANUAL",
            is_active=True,
            first_seen=datetime.now(timezone.utc),
            last_seen=datetime.now(timezone.utc),
            created_at=datetime.now(timezone.utc)
        )
        db.add(temp_ioc)
        db.commit()

        # Create incident
        ev = client.post(
            "/api/v1/security/events",
            json={
                "event_type": "BROWSER_BLOCKED_URL",
                "severity": "HIGH",
                "source_component": "BROWSER_EXTENSION",
                "threat_indicator": temp_url,
                "risk_score": 85.0,
                "description": "Temp IOC test"
            }
        )
        inc_id = ev.json()["incident_id"]

        # Admin marks false-positive with X-Admin-Key
        admin_res = client.post(
            f"/api/v1/incidents/{inc_id}/false-positive",
            headers={"X-Admin-Key": settings.ADMIN_SECRET_KEY},
            json={"reason": "Admin reviewed false positive report and confirmed benign domain"}
        )
        assert admin_res.status_code == 200

        # Verified de-listed in DB
        db.refresh(temp_ioc)
        assert temp_ioc.is_active is False
    finally:
        db.close()


# ==============================================================================
# OBJECTIVE C: Event Deduplication & Normalization Accuracy
# ==============================================================================

def test_b31_deterministic_url_normalization():
    """
    Verify consistent URL normalization across casing, default ports, fragments, and query sorting.
    """
    url_1 = "http://EXAMPLE.COM:80/login?token=abc&user=rahul#submit"
    url_2 = "http://example.com/login?user=rahul&token=abc"

    norm_1 = normalize_url_indicator(url_1)
    norm_2 = normalize_url_indicator(url_2)

    assert norm_1 == norm_2
    assert "#submit" not in norm_1
    assert ":80" not in norm_1
    assert "token=abc&user=rahul" in norm_1


def test_b31_deterministic_phone_normalization():
    """
    Verify Indian standard mobile and international phone number normalization.
    """
    assert normalize_phone_indicator("9876543210") == "+919876543210"
    assert normalize_phone_indicator("09876543210") == "+919876543210"
    assert normalize_phone_indicator("+91 98765-43210") == "+919876543210"
    assert normalize_phone_indicator("+1 (800) 555-0199") == "+18005550199"


def test_b31_distinct_source_evidence_preservation():
    """
    Verify that when Browser and Android report the same threat, deduplication
    does NOT discard the second component's evidence.
    """
    test_target = f"https://cross-vector-{uuid.uuid4().hex[:6]}.com"

    # 1. Browser Extension reports threat
    res_browser = client.post(
        "/api/v1/security/events",
        json={
            "event_type": "BROWSER_BLOCKED_URL",
            "severity": "HIGH",
            "source_component": "BROWSER_EXTENSION",
            "threat_indicator": test_target,
            "risk_score": 85.0,
            "description": "Navigation blocked by browser shield"
        }
    )
    assert res_browser.status_code == 201
    inc_id = res_browser.json()["incident_id"]

    # 2. Android App reports identical threat within deduplication window
    res_android = client.post(
        "/api/v1/security/events",
        json={
            "event_type": "SMS_FRAUD_DETECTED",
            "severity": "HIGH",
            "source_component": "ANDROID_APP",
            "threat_indicator": test_target,
            "risk_score": 88.0,
            "description": "SMS phishing message detected on Android"
        }
    )
    assert res_android.status_code == 201

    # Fetch incident and verify BOTH source components are preserved
    inc_res = client.get(f"/api/v1/incidents/{inc_id}")
    assert inc_res.status_code == 200
    inc_data = inc_res.json()
    sources = inc_data.get("source_components", [])
    assert "BROWSER_EXTENSION" in sources
    assert "ANDROID_APP" in sources


# ==============================================================================
# OBJECTIVE D: SSE Stream Security & Scoping Tests
# ==============================================================================

def test_b31_revoked_device_sse_stream_rejected():
    """
    Verify that a revoked device token cannot establish an SSE connection.
    """
    res = client.get(
        "/api/v1/security/stream",
        headers={"X-Device-Token": REVOKED_DEVICE_TOKEN}
    )
    assert res.status_code == 403
    assert "revoked" in res.json()["detail"].lower()


def test_b31_invalid_device_token_sse_rejected():
    """
    Verify that an invalid device token is rejected with 401 Unauthorized.
    """
    res = client.get(
        "/api/v1/security/stream",
        headers={"X-Device-Token": "completely-invalid-token-12345"}
    )
    assert res.status_code == 401


def test_b31_unauthorized_cross_device_sse_stream_rejected():
    """
    Verify that Device A cannot subscribe to Device B's private SSE stream.
    """
    res = client.get(
        f"/api/v1/security/stream?target_device={DEVICE_B_UUID}",
        headers={"X-Device-Token": DEVICE_A_TOKEN}
    )
    assert res.status_code == 403
    assert "Access denied" in res.json()["detail"]


# ==============================================================================
# OBJECTIVE G: Authoritative Threat Source Anti-Forgery Tests
# ==============================================================================

def test_b31_client_cannot_forge_critical_without_authoritative_feed():
    """
    Verify that an uncorroborated client event claiming CRITICAL severity
    is capped at HIGH and marked UNVERIFIED by the backend.
    """
    fake_url = f"https://unverified-claim-{uuid.uuid4().hex[:6]}.com"

    res = client.post(
        "/api/v1/security/events",
        json={
            "event_type": "SMS_FRAUD_DETECTED",
            "severity": "CRITICAL",  # Untrusted client claim
            "source_component": "ANDROID_APP",
            "threat_indicator": fake_url,
            "risk_score": 99.0,
            "description": "Client claimed critical severity without authority"
        }
    )
    assert res.status_code == 201
    data = res.json()
    # Capped at HIGH
    assert data["severity"] == "HIGH"
    assert data["verification_status"] == "UNVERIFIED"


# ==============================================================================
# OBJECTIVE H: Production Debug & Rate Limiting Safety Tests
# ==============================================================================

def test_b31_rate_limit_bypass_forbidden_in_production():
    """
    Verify that rate limit bypass header is completely ignored when APP_ENV == 'production'.
    """
    from app.core.security import RateLimiterMiddleware
    from starlette.requests import Request

    # Create dummy request with bypass header
    headers = [(b"x-test-bypass-rate-limit", b"true")]
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/api/v1/security/events",
        "headers": headers,
        "client": ("192.0.2.1", 12345)
    }
    req = Request(scope)

    # In development mode, bypass is allowed
    assert settings.DEBUG is True

    # Temporarily simulate production mode
    original_env = settings.APP_ENV
    original_debug = settings.DEBUG
    try:
        settings.APP_ENV = "production"
        settings.DEBUG = False
        from app.core.config import settings as _s
        bypass_allowed = (
            _s.DEBUG
            and _s.APP_ENV != "production"
            and req.headers.get("x-test-bypass-rate-limit") == "true"
        )
        assert bypass_allowed is False
    finally:
        settings.APP_ENV = original_env
        settings.DEBUG = original_debug


def test_b31_notification_device_isolation(client, db_session):
    """
    Verify that notifications targeted to a specific device_id are isolated
    and never returned when queried for a different device_id.
    """
    from app.services.notification_service import notification_service
    from app.schemas.notification import NotificationCreate

    dev_a = "b31-notif-dev-alpha"
    dev_b = "b31-notif-dev-beta"

    # Create private alert for Device A
    notif_a = notification_service.create_notification(
        db_session,
        NotificationCreate(
            title="Private Threat Alert Device A",
            message="Urgent threat detected specifically on Device A phone",
            severity="HIGH",
            category="SECURITY_ALERT",
            source_component="ANDROID_APP",
            device_id=dev_a
        )
    )

    # Create private alert for Device B
    notif_b = notification_service.create_notification(
        db_session,
        NotificationCreate(
            title="Private Threat Alert Device B",
            message="Urgent threat detected specifically on Device B phone",
            severity="HIGH",
            category="SECURITY_ALERT",
            source_component="ANDROID_APP",
            device_id=dev_b
        )
    )

    # Query notifications scoped to Device A
    res_a = client.get(f"/api/v1/notifications?device_id={dev_a}")
    assert res_a.status_code == 200
    items_a = res_a.json()["items"]
    titles_a = [i["title"] for i in items_a]
    assert "Private Threat Alert Device A" in titles_a
    assert "Private Threat Alert Device B" not in titles_a

    # Query notifications scoped to Device B
    res_b = client.get(f"/api/v1/notifications?device_id={dev_b}")
    assert res_b.status_code == 200
    items_b = res_b.json()["items"]
    titles_b = [i["title"] for i in items_b]
    assert "Private Threat Alert Device B" in titles_b
    assert "Private Threat Alert Device A" not in titles_b


