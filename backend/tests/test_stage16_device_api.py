"""
Stage 16: Mobile Device Management API Tests
Phase B1: Native Android Foundation
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database.session import init_db

# Ensure all database tables exist and migrations run
init_db()

client = TestClient(app)

TEST_DEVICE_ID = "a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d"
TEST_DEVICE_NAME = "Google Pixel 8 - Android 14"


def test_device_registration_success():
    """Valid UUID registration must succeed with status 200 and ACTIVE status."""
    payload = {
        "device_id": TEST_DEVICE_ID,
        "device_name": TEST_DEVICE_NAME,
        "app_version": "1.0.0"
    }
    response = client.post("/api/v1/devices/register", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["device_id"] == TEST_DEVICE_ID
    assert data["device_name"] == TEST_DEVICE_NAME
    assert data["status"] == "ACTIVE"
    assert data["security_posture"] == "PROTECTED"
    assert "modules" in data
    assert data["modules"]["browser_protection"] == "ACTIVE"
    assert data["modules"]["threat_intelligence"] == "ACTIVE"
    assert data["modules"]["security_notifications"] == "ACTIVE"
    assert data["modules"]["mobile_protection"] == "ACTIVE"


def test_device_registration_idempotent():
    """Re-registering same device updates device_name and last_seen_at without duplicate key error."""
    payload = {
        "device_id": TEST_DEVICE_ID,
        "device_name": "Google Pixel 8 Pro - Android 15",
        "app_version": "1.0.1"
    }
    response = client.post("/api/v1/devices/register", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["device_name"] == "Google Pixel 8 Pro - Android 15"
    assert data["app_version"] == "1.0.1"


def test_device_status_success():
    """Fetching device status returns correct posture and updates last_seen_at."""
    response = client.get(f"/api/v1/devices/{TEST_DEVICE_ID}/status")
    assert response.status_code == 200
    data = response.json()
    assert data["device_id"] == TEST_DEVICE_ID
    assert data["status"] == "ACTIVE"
    assert data["security_posture"] == "PROTECTED"
    assert data["last_seen_at"] is not None


def test_device_status_not_found():
    """Fetching unknown device returns 404."""
    response = client.get("/api/v1/devices/00000000-0000-0000-0000-000000000000/status")
    assert response.status_code == 404
    assert "not registered" in response.json()["detail"]


def test_device_activity_success():
    """Fetching device activity feed returns events list."""
    response = client.get(f"/api/v1/devices/{TEST_DEVICE_ID}/activity?limit=10")
    assert response.status_code == 200
    data = response.json()
    assert data["device_id"] == TEST_DEVICE_ID
    assert "events" in data
    assert "total_events" in data


def test_device_activity_not_found():
    """Fetching activity for unregistered device returns 404."""
    response = client.get("/api/v1/devices/00000000-0000-0000-0000-000000000000/activity")
    assert response.status_code == 404


def test_device_registration_rejects_imei():
    """Hardware IMEIs (14-16 digits) must be strictly rejected with 422."""
    payload = {
        "device_id": "864123456789012",  # 15 digits IMEI
        "device_name": "Insecure Phone",
        "app_version": "1.0.0"
    }
    response = client.post("/api/v1/devices/register", json=payload)
    assert response.status_code == 422


def test_device_registration_rejects_phone_number():
    """Phone numbers must be strictly rejected with 422."""
    payload = {
        "device_id": "+1-800-555-0199",
        "device_name": "Insecure Phone",
        "app_version": "1.0.0"
    }
    response = client.post("/api/v1/devices/register", json=payload)
    assert response.status_code == 422


def test_device_registration_rejects_short_id():
    """Device IDs shorter than 16 characters must be rejected with 422."""
    payload = {
        "device_id": "too-short",
        "device_name": "Insecure Phone",
        "app_version": "1.0.0"
    }
    response = client.post("/api/v1/devices/register", json=payload)
    assert response.status_code == 422

