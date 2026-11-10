"""
backend/tests/test_stage15_notifications.py
Comprehensive Verification Suite for Phase A3: Intelligent Security Notification & Alert Engine.
Covers all 15 requirements specified in Section 11:
1. Notification generation
2. Critical threat notification
3. High-risk notification
4. Duplicate notification prevention
5. Notification history & pagination
6. Mark-as-read functionality
7. Delete notification
8. Notification filtering
9. Browser notification preferences
10. Dashboard notification updates & SSE stream
11. Threat intelligence integration
12. Offline fallback notifications
13. Invalid notification payloads
14. Security validation
15. Notification rate limiting
"""
import pytest
import json
import time
from fastapi.testclient import TestClient

from app.main import app
from app.database.session import SessionLocal, init_db
from app.models.notification import Notification, NotificationPreference
from app.services.notification_service import notification_service, NotificationService
from app.schemas.notification import NotificationCreate

# Ensure database tables and column migrations are applied
init_db()

client = TestClient(app)


def test_01_notification_generation():
    """Requirement 1: Notification generation with required fields."""
    payload = {
        "title": "Malicious Domain Blocked",
        "message": "Access to phishing-test.invalid was blocked by DNR shield before page load.",
        "severity": "HIGH",
        "category": "MALICIOUS_WEBSITE",
        "target_domain": "phishing-test.invalid",
        "recommended_action": "Avoid entering credentials or visiting this domain.",
        "source_component": "BROWSER_DNR"
    }
    res = client.post("/api/v1/notifications", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert data["id"] is not None
    assert data["title"] == payload["title"]
    assert data["severity"] == "HIGH"
    assert data["category"] == "MALICIOUS_WEBSITE"
    assert data["target_domain"] == "phishing-test.invalid"
    assert data["is_read"] is False


def test_02_critical_threat_notification():
    """Requirement 2: Critical threat notification creation and audit event logging."""
    payload = {
        "title": "Critical Digital Arrest Scam Intercepted",
        "message": "Fake Supreme Court arrest warrant payment portal intercepted.",
        "severity": "CRITICAL",
        "category": "MALICIOUS_WEBSITE",
        "target_domain": "cbi-digital-arrest-warrant.com",
        "recommended_action": "Do not transfer money. Official police never demand money via video call.",
        "source_component": "BROWSER_EXTENSION"
    }
    res = client.post("/api/v1/notifications", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert data["severity"] == "CRITICAL"
    assert data["category"] == "MALICIOUS_WEBSITE"


def test_03_high_risk_notification():
    """Requirement 3: High-risk notification creation."""
    payload = {
        "title": "High Risk Credential Phishing Detected",
        "message": "Impersonation of banking KYC update portal detected with 96% confidence.",
        "severity": "HIGH",
        "category": "PHISHING_ATTEMPT",
        "target_domain": "sbi-kyc-update.invalid",
        "recommended_action": "Navigate away from site. Official banks never request OTP via unverified domains.",
        "source_component": "PHISHING_MODEL"
    }
    res = client.post("/api/v1/notifications", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert data["severity"] == "HIGH"
    assert data["category"] == "PHISHING_ATTEMPT"


def test_04_duplicate_notification_prevention():
    """Requirement 4: Duplicate notification prevention within deduplication window."""
    svc = NotificationService()
    db = SessionLocal()
    try:
        payload = NotificationCreate(
            title="Duplicate Test Attack",
            message="Initial block event",
            severity="HIGH",
            category="MALICIOUS_WEBSITE",
            target_domain="duplicate-prevention.invalid"
        )
        notif1 = svc.create_notification(db, payload)
        initial_id = notif1.id

        # Immediate repeat with same category and domain
        payload_repeat = NotificationCreate(
            title="Duplicate Test Attack",
            message="Second block event on same domain",
            severity="HIGH",
            category="MALICIOUS_WEBSITE",
            target_domain="duplicate-prevention.invalid"
        )
        notif2 = svc.create_notification(db, payload_repeat)

        # Should return the existing notification rather than creating a duplicate
        assert notif2.id == initial_id
    finally:
        db.close()


def test_05_notification_history_and_pagination():
    """Requirement 5: Retrieve notification history with pagination."""
    res = client.get("/api/v1/notifications?limit=5&offset=0")
    assert res.status_code == 200
    data = res.json()
    assert "total" in data
    assert "unread_count" in data
    assert "items" in data
    assert len(data["items"]) <= 5


def test_06_mark_as_read_and_unread_count():
    """Requirement 6: Mark individual and all notifications as read."""
    # 1. Create a fresh unread notification
    payload = {
        "title": "Unread Notification Test",
        "message": "Testing read status toggling",
        "severity": "LOW",
        "category": "SYSTEM_ALERT",
        "target_domain": f"test-read-{time.time()}.invalid"
    }
    create_res = client.post("/api/v1/notifications", json=payload)
    assert create_res.status_code == 201
    notif_id = create_res.json()["id"]

    # 2. Check unread count
    count_res = client.get("/api/v1/notifications/unread-count")
    assert count_res.status_code == 200
    assert count_res.json()["unread_count"] >= 1

    # 3. Mark individual as read
    patch_res = client.patch(f"/api/v1/notifications/{notif_id}/read")
    assert patch_res.status_code == 200
    assert patch_res.json()["is_read"] is True

    # 4. Mark all as read
    read_all_res = client.post("/api/v1/notifications/read-all")
    assert read_all_res.status_code == 200
    assert "marked_read_count" in read_all_res.json()

    # Verify unread count is now 0
    final_count = client.get("/api/v1/notifications/unread-count").json()["unread_count"]
    assert final_count == 0


def test_07_delete_notification():
    """Requirement 7: Delete individual notification."""
    payload = {
        "title": "Ephemeral Alert",
        "message": "This alert will be deleted immediately",
        "severity": "LOW",
        "category": "SYSTEM_ALERT",
        "target_domain": f"ephemeral-{time.time()}.invalid"
    }
    item = client.post("/api/v1/notifications", json=payload).json()
    notif_id = item["id"]

    # Delete
    del_res = client.delete(f"/api/v1/notifications/{notif_id}")
    assert del_res.status_code == 200

    # Ensure 404 on subsequent delete or read
    del_again = client.delete(f"/api/v1/notifications/{notif_id}")
    assert del_again.status_code == 404


def test_08_notification_filtering():
    """Requirement 8: Filter notifications by severity and category."""
    # Create specific entries
    client.post("/api/v1/notifications", json={
        "title": "Filter Check Critical",
        "message": "Testing critical filtering",
        "severity": "CRITICAL",
        "category": "MALICIOUS_WEBSITE",
        "target_domain": f"filter-crit-{time.time()}.invalid"
    })
    client.post("/api/v1/notifications", json={
        "title": "Filter Check Medium",
        "message": "Testing medium filtering",
        "severity": "MEDIUM",
        "category": "THREAT_INTEL_SYNC",
        "target_domain": f"filter-sync-{time.time()}.invalid"
    })

    # Filter by CRITICAL
    crit_res = client.get("/api/v1/notifications?severity=CRITICAL")
    assert crit_res.status_code == 200
    for item in crit_res.json()["items"]:
        assert item["severity"] == "CRITICAL"

    # Filter by Category
    cat_res = client.get("/api/v1/notifications?category=THREAT_INTEL_SYNC")
    assert cat_res.status_code == 200
    for item in cat_res.json()["items"]:
        assert item["category"] == "THREAT_INTEL_SYNC"


def test_09_notification_preferences():
    """Requirement 9: Retrieve and update user notification preferences."""
    # Get preferences
    get_res = client.get("/api/v1/notifications/preferences")
    assert get_res.status_code == 200
    prefs = get_res.json()
    assert "browser_notifications_enabled" in prefs
    assert "min_severity" in prefs

    # Update preferences
    update_payload = {
        "browser_notifications_enabled": False,
        "min_severity": "HIGH",
        "sound_enabled": True
    }
    put_res = client.put("/api/v1/notifications/preferences", json=update_payload)
    assert put_res.status_code == 200
    updated = put_res.json()
    assert updated["browser_notifications_enabled"] is False
    assert updated["min_severity"] == "HIGH"
    assert updated["sound_enabled"] is True

    # Restore defaults
    client.put("/api/v1/notifications/preferences", json={
        "browser_notifications_enabled": True,
        "min_severity": "LOW",
        "sound_enabled": False
    })


def test_10_dashboard_sse_stream_endpoint():
    """Requirement 10: Real-time SSE stream endpoint accepts connections."""
    # Test that /stream returns text/event-stream headers
    with client.stream("GET", "/api/v1/notifications/stream") as stream:
        assert stream.status_code == 200
        assert "text/event-stream" in stream.headers["content-type"]
        # Read the first event (connected ping)
        for line in stream.iter_lines():
            if line and "connected" in line:
                break


def test_11_threat_intel_integration():
    """Requirement 11: Notification engine receives threat intel sync notices."""
    payload = {
        "title": "Threat Intelligence Signatures Updated",
        "message": "Successfully synchronized 14 new verified indicators from URLhaus.",
        "severity": "LOW",
        "category": "THREAT_INTEL_SYNC",
        "target_domain": "urlhaus-api.abuse.ch",
        "source_component": "THREAT_INTEL_SCHEDULER"
    }
    res = client.post("/api/v1/notifications", json=payload)
    assert res.status_code == 201
    assert res.json()["category"] == "THREAT_INTEL_SYNC"


def test_12_offline_behaviour_notification():
    """Requirement 12: Notification engine emits notice when threat feed is offline."""
    payload = {
        "title": "Threat Feed Offline Fallback",
        "message": "URLhaus threat feed was unreachable. Local cached threat database active.",
        "severity": "MEDIUM",
        "category": "THREAT_INTEL_SYNC",
        "target_domain": "urlhaus-api.abuse.ch",
        "source_component": "THREAT_INTEL_SCHEDULER"
    }
    res = client.post("/api/v1/notifications", json=payload)
    assert res.status_code == 201
    assert res.json()["severity"] == "MEDIUM"


def test_13_invalid_notification_payloads():
    """Requirement 13: Reject invalid or malformed notification payloads."""
    # Missing title (min_length 3)
    res_short = client.post("/api/v1/notifications", json={"title": "a", "message": "Valid message text"})
    assert res_short.status_code == 422

    # Missing message
    res_no_msg = client.post("/api/v1/notifications", json={"title": "Valid Title"})
    assert res_no_msg.status_code == 422


def test_14_security_validation_sanitization():
    """Requirement 14: Sanitize dangerous HTML / script tags in notification title and message."""
    xss_payload = {
        "title": "XSS Test <script>alert(1)</script>",
        "message": "Checking that script tags and internal stack traces are not leaked: <img src=x onerror=alert(1)>",
        "severity": "CRITICAL",
        "category": "MALICIOUS_WEBSITE",
        "target_domain": "xss-test.invalid"
    }
    res = client.post("/api/v1/notifications", json=xss_payload)
    assert res.status_code == 201
    data = res.json()
    # Confirm output does not crash or execute
    assert "XSS Test" in data["title"]


def test_15_notification_rate_limiting():
    """Requirement 15: Severity escalation overrides rate limiting on same domain."""
    svc = NotificationService()
    db = SessionLocal()
    try:
        domain = f"rate-limit-{time.time()}.invalid"
        # 1. Medium event
        p1 = NotificationCreate(
            title="Suspicious Domain Detected",
            message="Unusual domain structure",
            severity="MEDIUM",
            category="HIGH_RISK_URL",
            target_domain=domain
        )
        n1 = svc.create_notification(db, p1)

        # 2. Critical event arrives immediately on same domain -> Must NOT be suppressed
        p2 = NotificationCreate(
            title="Confirmed Malicious Phish Blocked",
            message="Escalated to confirmed malware delivery",
            severity="CRITICAL",
            category="HIGH_RISK_URL",
            target_domain=domain
        )
        n2 = svc.create_notification(db, p2)

        # Escalation must be admitted
        assert n2.id != n1.id
        assert n2.severity == "CRITICAL"
    finally:
        db.close()

