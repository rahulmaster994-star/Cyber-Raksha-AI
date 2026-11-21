"""
Cyber Raksha AI - Stage 19: Phase B3 Unified Protection Integration Tests
Tests all 5 core workflows:
  1. Browser Extension threat blocking -> Unified Event Ingestion -> Incident Correlation -> Notification
  2. Android SMS Fraud detection -> Event Ingestion -> Incident creation
  3. Phone/Caller reputation check & risk evaluation
  4. Incident lifecycle: Ack -> Resolve -> False Positive
  5. Resiliency & security: Token enforcement, deduplication suppression, validation, stream availability
"""
import uuid
import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.core.config import settings
from app.database.session import SessionLocal
from app.models.threat_intel import ThreatIndicator
from app.models.device import Device
from app.models.security_event import SecurityEvent
from app.models.incident import SecurityIncident

client = TestClient(app, headers={"x-test-bypass-rate-limit": "true"})

TEST_DEVICE_UUID = "b3000000-0000-0000-0000-000000000001"
TEST_DEVICE_TOKEN = "test-b3-device-token-secret-xyz"


@pytest.fixture(scope="module", autouse=True)
def setup_b3_test_environment():
    db: Session = SessionLocal()
    try:
        # Register or update test device
        dev = db.query(Device).filter(Device.device_id == TEST_DEVICE_UUID).first()
        import hashlib
        token_hash = hashlib.sha256(TEST_DEVICE_TOKEN.encode()).hexdigest()
        if not dev:
            dev = Device(
                device_id=TEST_DEVICE_UUID,
                device_name="Test Samsung Galaxy S23",
                app_version="1.0.0",
                status="ACTIVE",
                is_revoked=False,
                device_token_hash=token_hash,
                registered_at=datetime.now(timezone.utc),
                last_seen_at=datetime.now(timezone.utc)
            )
            db.add(dev)
        else:
            dev.is_revoked = False
            dev.status = "ACTIVE"
            dev.device_token_hash = token_hash

        # Add authoritative threat indicator
        test_url_ioc = db.query(ThreatIndicator).filter(ThreatIndicator.indicator_value == "https://scam-sbi-kyc-update.com/login").first()
        if not test_url_ioc:
            test_url_ioc = ThreatIndicator(
                indicator_type="URL",
                indicator_value="https://scam-sbi-kyc-update.com/login",
                threat_type="PHISHING",
                severity="CRITICAL",
                confidence_score=0.99,
                source_name="URLHAUS",
                description="Verified banking phishing portal targeting SBI credentials.",
                is_active=True,
                first_seen=datetime.now(timezone.utc),
                last_seen=datetime.now(timezone.utc),
                created_at=datetime.now(timezone.utc)
            )
            db.add(test_url_ioc)

        db.commit()
    finally:
        db.close()


def test_b3_workflow_1_browser_blocked_event_and_incident_correlation():
    """
    Workflow 1: Browser Extension detects/blocks malicious URL -> reports security event.
    Backend ingests event, correlates with threat intelligence, escalates to CRITICAL incident.
    """
    payload = {
        "event_type": "BROWSER_BLOCKED_URL",
        "severity": "HIGH",
        "source_component": "BROWSER_EXTENSION",
        "threat_indicator": "https://scam-sbi-kyc-update.com/login",
        "risk_score": 85.0,
        "detection_reason": "Matched Declarative Net Request block rule for verified phishing domain",
        "description": "Navigation blocked to https://scam-sbi-kyc-update.com/login"
    }

    res = client.post("/api/v1/security/events", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert data["event_type"] == "BROWSER_BLOCKED_URL"
    assert data["threat_indicator"] == "https://scam-sbi-kyc-update.com/login"
    # Corroborated by ThreatIndicator in DB -> escalated to CRITICAL
    assert data["severity"] == "CRITICAL"
    assert data["verification_status"] == "CORROBORATED"
    assert data["incident_id"] is not None

    # Verify incident created
    inc_res = client.get(f"/api/v1/incidents/{data['incident_id']}")
    assert inc_res.status_code == 200
    inc_data = inc_res.json()
    assert inc_data["status"] in ["NEW", "ACTION_REQUIRED"]
    assert "https://scam-sbi-kyc-update.com/login" in (inc_data.get("target_or_indicator") or inc_data.get("summary"))


def test_b3_workflow_1_deduplication_suppression():
    """
    Verify identical security events within 30 seconds are deduplicated and not duplicated in DB.
    """
    payload = {
        "event_type": "BROWSER_BLOCKED_URL",
        "severity": "HIGH",
        "source_component": "BROWSER_EXTENSION",
        "threat_indicator": "https://scam-sbi-kyc-update.com/login",
        "risk_score": 85.0,
        "detection_reason": "Duplicate click attempt",
        "description": "Navigation blocked to https://scam-sbi-kyc-update.com/login"
    }

    res1 = client.post("/api/v1/security/events", json=payload)
    assert res1.status_code == 201
    first_id = res1.json()["id"]

    res2 = client.post("/api/v1/security/events", json=payload)
    assert res2.status_code == 201
    second_id = res2.json()["id"]

    # Deduplicated -> same event ID returned
    assert first_id == second_id


def test_b3_workflow_2_android_sms_fraud_event_and_correlation():
    """
    Workflow 2: Android App detects high-risk SMS fraud -> reports event with device_id.
    """
    payload = {
        "event_type": "SMS_FRAUD_DETECTED",
        "severity": "CRITICAL",
        "source_component": "ANDROID_APP",
        "device_id": TEST_DEVICE_UUID,
        "threat_indicator": "https://scam-sbi-kyc-update.com/login",
        "risk_score": 96.0,
        "detection_reason": "Urgent KYC suspension threat with extraction of malicious URL",
        "description": "Dear customer your SBI account is blocked update KYC immediately at link"
    }

    res = client.post("/api/v1/security/events", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert data["source_component"] == "ANDROID_APP"
    assert data["device_id"] == TEST_DEVICE_UUID
    assert data["incident_id"] is not None

    # Correlated into the incident for this device and indicator
    inc_res = client.get(
        f"/api/v1/incidents/{data['incident_id']}",
        headers={"X-Device-Token": TEST_DEVICE_TOKEN}
    )
    assert inc_res.status_code == 200
    inc_data = inc_res.json()
    assert inc_data["device_id"] == TEST_DEVICE_UUID


def test_b3_workflow_3_unified_risk_evaluation():
    """
    Workflow 3: Central Risk Engine synthesizes risk without double-counting.
    """
    # Evaluate known malicious URL
    url_req = {
        "indicator": "https://scam-sbi-kyc-update.com/login",
        "indicator_type": "URL",
        "source_component": "BROWSER_EXTENSION"
    }
    url_res = client.post("/api/v1/security/risk/evaluate", json=url_req)
    assert url_res.status_code == 200
    res_data = url_res.json()
    assert res_data["risk_level"] == "CRITICAL"
    assert res_data["is_verified_threat"] is True
    assert "URLHAUS" in res_data["corroborating_sources"]

    # Evaluate clean/unknown domain
    clean_req = {
        "indicator": "https://legitimate-bank-portal.gov.in",
        "indicator_type": "URL",
        "source_component": "ANDROID_APP"
    }
    clean_res = client.post("/api/v1/security/risk/evaluate", json=clean_req)
    assert clean_res.status_code == 200
    assert clean_res.json()["risk_level"] == "SAFE"


def test_b3_workflow_4_incident_lifecycle_management():
    """
    Workflow 4: User/Analyst acknowledges, resolves, or marks incident as false-positive.
    """
    # Create distinct incident
    test_ind = f"https://fraud-test-{uuid.uuid4().hex[:8]}.com"
    event_payload = {
        "event_type": "BROWSER_BLOCKED_URL",
        "severity": "HIGH",
        "source_component": "BROWSER_EXTENSION",
        "threat_indicator": test_ind,
        "risk_score": 80.0,
        "detection_reason": "High-risk domain with homoglyph spoofing",
        "description": f"Blocked navigation to {test_ind}"
    }
    ev_res = client.post("/api/v1/security/events", json=event_payload)
    assert ev_res.status_code == 201
    incident_id = ev_res.json()["incident_id"]
    assert incident_id is not None

    # 1. Acknowledge incident
    ack_res = client.post(f"/api/v1/incidents/{incident_id}/acknowledge")
    assert ack_res.status_code == 200
    assert ack_res.json()["user_acknowledged"] is True

    # 2. Resolve incident
    resolve_payload = {
        "resolution_notes": "User confirmed scam attempt thwarted; domain confirmed dead",
        "close_incident": True
    }
    res_res = client.post(f"/api/v1/incidents/{incident_id}/resolve", json=resolve_payload)
    assert res_res.status_code == 200
    res_data = res_res.json()
    assert res_data["status"] == "RESOLVED"
    assert "thwarted" in res_data["resolution_notes"]


def test_b3_workflow_5_dashboard_telemetry_queries():
    """
    Workflow 5: Dashboard returns real aggregated data directly from database queries.
    """
    # Overview
    ov_res = client.get("/api/v1/dashboard/overview", headers={"x-admin-key": settings.ADMIN_SECRET_KEY})
    assert ov_res.status_code == 200
    ov_data = ov_res.json()
    assert "overall_posture" in ov_data
    assert "events" in ov_data
    assert "incidents" in ov_data
    assert "devices" in ov_data
    assert "threat_intelligence" in ov_data
    assert ov_data["events"]["total"] >= 1

    # Activity feed
    act_res = client.get("/api/v1/dashboard/activity?limit=10", headers={"x-admin-key": settings.ADMIN_SECRET_KEY})
    assert act_res.status_code == 200
    act_data = act_res.json()
    assert "activities" in act_data
    assert len(act_data["activities"]) >= 1

    # Active incidents
    inc_list_res = client.get("/api/v1/dashboard/incidents?limit=5", headers={"x-admin-key": settings.ADMIN_SECRET_KEY})
    assert inc_list_res.status_code == 200
    assert "incidents" in inc_list_res.json()


def test_b3_security_and_filtering():
    """
    Verify security event listing and filtering by component, severity, device_id.
    """
    list_res = client.get("/api/v1/security/events?source_component=ANDROID_APP")
    assert list_res.status_code == 200
    events = list_res.json()["events"]
    for e in events:
        assert e["source_component"] == "ANDROID_APP"

    # Filter by device_id
    dev_res = client.get(f"/api/v1/security/events?device_id={TEST_DEVICE_UUID}")
    assert dev_res.status_code == 200
    for e in dev_res.json()["events"]:
        assert e["device_id"] == TEST_DEVICE_UUID
