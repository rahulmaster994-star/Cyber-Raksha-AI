"""
Cyber Raksha AI - Admin SOC & Security Hardening Integration Tests
Tests all Section 4 Admin Control Room endpoints, authorization gates,
audit logging, device revocation authorization, and dashboard telemetry protection.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.base import Base
from app.database.session import get_db
from app.main import app
from app.core.config import settings
from app.models.user import User
from app.models.device import Device
from app.models.security_event import SecurityEvent
from app.models.incident import SecurityIncident
from app.core.auth_utils import hash_password, create_access_token

TEST_DATABASE_URL = "sqlite:///./test_admin_soc.db"
test_engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


client = TestClient(app)

ADMIN_KEY = settings.ADMIN_SECRET_KEY


@pytest.fixture(scope="module", autouse=True)
def setup_db():
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    app.dependency_overrides[get_db] = override_get_db
    db = TestingSessionLocal()

    # Seed test users
    admin_user = User(
        email="admin@cyberraksha.ai",
        username="admin_soc",
        hashed_password=hash_password("AdminSecurePass123!"),
        role="admin",
        is_active=True
    )
    citizen_user = User(
        email="citizen@example.com",
        username="citizen_user",
        hashed_password=hash_password("CitizenPass123!"),
        mobile_number="+919876543210",
        role="citizen",
        is_active=True
    )
    db.add(admin_user)
    db.add(citizen_user)

    # Seed test device
    device = Device(
        device_id="android-test-device-01",
        device_name="Samsung Galaxy Test",
        app_version="1.0.0",
        status="ACTIVE",
        security_posture="PROTECTED"
    )
    db.add(device)
    db.commit()
    db.close()

    yield

    app.dependency_overrides.pop(get_db, None)
    Base.metadata.drop_all(bind=test_engine)


def test_01_admin_unauthorized_access_rejected():
    """Unauthenticated calls to /admin/overview must return 401."""
    res = client.get("/api/v1/admin/overview")
    assert res.status_code == 401
    assert "Administrator authentication required" in res.json().get("detail", "")


def test_02_admin_invalid_key_rejected():
    """Calls with incorrect X-Admin-Key must return 401."""
    res = client.get("/api/v1/admin/overview", headers={"X-Admin-Key": "wrong-secret-key"})
    assert res.status_code == 401


def test_03_admin_login_with_key():
    """Login via valid admin_key returns short-lived admin JWT."""
    res = client.post("/api/v1/admin/auth/login", json={"admin_key": ADMIN_KEY})
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["role"] == "admin"


def test_04_admin_login_with_credentials():
    """Login via database admin user credentials returns admin JWT."""
    res = client.post("/api/v1/admin/auth/login", json={
        "username": "admin_soc",
        "password": "AdminSecurePass123!"
    })
    assert res.status_code == 200
    assert "access_token" in res.json()


def test_05_admin_verify_session():
    """Admin verify route returns authenticated status."""
    res = client.get("/api/v1/admin/auth/verify", headers={"X-Admin-Key": ADMIN_KEY})
    assert res.status_code == 200
    assert res.json().get("status") == "AUTHENTICATED"


def test_06_admin_overview_telemetry():
    """Admin overview returns real backend metrics."""
    res = client.get("/api/v1/admin/overview", headers={"X-Admin-Key": ADMIN_KEY})
    assert res.status_code == 200
    data = res.json()
    assert "users" in data
    assert "devices" in data
    assert "events" in data
    assert "incidents" in data
    assert data["users"]["total"] >= 2
    assert data["devices"]["total_registered"] >= 1


def test_07_admin_users_directory_and_status():
    """Admin user directory lists users with privacy masking and supports status toggle."""
    res = client.get("/api/v1/admin/users", headers={"X-Admin-Key": ADMIN_KEY})
    assert res.status_code == 200
    users = res.json().get("users", [])
    assert len(users) >= 2
    # Verify email masking
    for u in users:
        assert "***" in u["email_masked"]

    # Toggle citizen user status
    citizen = next(u for u in users if u["username"] == "citizen_user")
    patch_res = client.patch(
        f"/api/v1/admin/users/{citizen['id']}/status",
        json={"is_active": False},
        headers={"X-Admin-Key": ADMIN_KEY}
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["is_active"] is False


def test_08_admin_devices_management():
    """Admin can list devices, inspect activity, and suspend/revoke device."""
    res = client.get("/api/v1/admin/devices", headers={"X-Admin-Key": ADMIN_KEY})
    assert res.status_code == 200
    devices = res.json().get("devices", [])
    assert len(devices) >= 1

    # Suspend device
    suspend_res = client.post(
        "/api/v1/admin/devices/android-test-device-01/suspend",
        headers={"X-Admin-Key": ADMIN_KEY}
    )
    assert suspend_res.status_code == 200
    assert suspend_res.json()["status"] == "SUSPENDED"


def test_09_admin_incidents_management():
    """Admin can create, list, and update incidents."""
    create_res = client.post(
        "/api/v1/admin/incidents",
        json={
            "category": "DIGITAL_ARREST",
            "title": "Suspected CBI Video Call Extortion",
            "severity": "CRITICAL",
            "summary": "Target received fraudulent CBI summons on WhatsApp.",
            "target_or_indicator": "+919988776655"
        },
        headers={"X-Admin-Key": ADMIN_KEY}
    )
    assert create_res.status_code == 201
    inc_data = create_res.json()
    incident_id = inc_data["id"]

    # Update incident status
    update_res = client.patch(
        f"/api/v1/admin/incidents/{incident_id}",
        json={"status": "INVESTIGATING", "resolution_notes": "Assigned to cyber cell."},
        headers={"X-Admin-Key": ADMIN_KEY}
    )
    assert update_res.status_code == 200
    assert update_res.json()["status"] == "INVESTIGATING"


def test_10_admin_threat_intelligence_crud():
    """Admin can add and deactivate threat indicators."""
    add_res = client.post(
        "/api/v1/admin/threat-intelligence/indicators",
        json={
            "indicator_type": "URL",
            "indicator_value": "http://fraud-sbi-portal.xyz/login",
            "threat_type": "PHISHING",
            "source_name": "ADMIN_VERIFIED",
            "confidence": 0.99
        },
        headers={"X-Admin-Key": ADMIN_KEY}
    )
    assert add_res.status_code == 201
    ind_id = add_res.json()["id"]

    # Deactivate indicator
    del_res = client.delete(
        f"/api/v1/admin/threat-intelligence/indicators/{ind_id}",
        headers={"X-Admin-Key": ADMIN_KEY}
    )
    assert del_res.status_code == 200
    assert del_res.json()["is_active"] is False


def test_11_dashboard_endpoints_require_admin_authorization():
    """SEC FIX VERIFICATION: /dashboard/overview, /activity, /incidents must reject unauthenticated requests."""
    res_overview = client.get("/api/v1/dashboard/overview")
    assert res_overview.status_code == 401

    res_activity = client.get("/api/v1/dashboard/activity")
    assert res_activity.status_code == 401

    res_incidents = client.get("/api/v1/dashboard/incidents")
    assert res_incidents.status_code == 401

    # Valid admin key succeeds
    res_auth = client.get("/api/v1/dashboard/overview", headers={"X-Admin-Key": ADMIN_KEY})
    assert res_auth.status_code == 200


def test_12_device_revocation_requires_authorization():
    """SEC FIX VERIFICATION: POST /devices/{id}/revoke must reject unauthenticated calls."""
    res = client.post("/api/v1/devices/android-test-device-01/revoke")
    assert res.status_code == 401

    # Revoke with admin key succeeds
    res_auth = client.post(
        "/api/v1/devices/android-test-device-01/revoke",
        headers={"X-Admin-Key": ADMIN_KEY}
    )
    assert res_auth.status_code == 200
    assert res_auth.json()["status"] == "REVOKED"


def test_13_admin_audit_logs_recorded():
    """All administrative actions must be persisted in admin_audit_logs table."""
    res = client.get("/api/v1/admin/audit-logs", headers={"X-Admin-Key": ADMIN_KEY})
    assert res.status_code == 200
    logs = res.json().get("logs", [])
    assert len(logs) >= 3  # Login, User update, Device suspend/revoke, Incident create
    actions = [lg["action"] for lg in logs]
    assert "INCIDENT_CREATED" in actions
    assert "IOC_CREATED" in actions
