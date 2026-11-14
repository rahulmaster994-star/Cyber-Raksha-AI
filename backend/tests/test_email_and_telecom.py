"""
Cyber Raksha AI - Email & Telecom SMS Verification Tests
Tests: Email service (4 notification types), Telecom SMS gateway states, and Account Deletion.
"""
import pytest
from app.services.email_service import email_service
from app.services.otp_service import otp_service, normalize_indian_mobile


def test_email_service_all_four_types():
    recipient = "citizen@example.com"

    # 1. Registration verification email
    r1 = email_service.send_verification_email(recipient, "secure-token-12345", "Rajesh Kumar")
    assert r1 is True
    last1 = email_service.outbox_history[-1]
    assert last1["to"] == recipient
    assert "Verify Your Cyber Raksha AI Account" in last1["subject"]
    assert "https://cyberraksha-backend.onrender.com/api/v1/auth/verify-email?token=" in last1["body_text"]

    # 2. Security alerts email
    r2 = email_service.send_security_alert_email(
        to_email=recipient,
        threat_type="DIGITAL_ARREST",
        severity="CRITICAL",
        details="Extortion scam call intercepted from fake police department."
    )
    assert r2 is True
    last2 = email_service.outbox_history[-1]
    assert "CRITICAL ALERT" in last2["subject"]
    assert "1930" in last2["body_text"]

    # 3. Complaint acknowledgement recording email
    r3 = email_service.send_complaint_confirmation_email(
        to_email=recipient,
        complaint_id="CR-CMP-2026-9999",
        category="BANKING_FRAUD",
        official_ack_number="ACK-1930-2026-001"
    )
    assert r3 is True
    last3 = email_service.outbox_history[-1]
    assert "CR-CMP-2026-9999" in last3["subject"]
    assert "ACK-1930-2026-001" in last3["body_text"]

    # 4. Verified complaint status update email
    r4 = email_service.send_complaint_status_email(
        to_email=recipient,
        complaint_id="CR-CMP-2026-9999",
        new_status="ACTION_TAKEN",
        notes="Bank account freeze request processed under Section 1930."
    )
    assert r4 is True
    last4 = email_service.outbox_history[-1]
    assert "ACTION_TAKEN" in last4["subject"]


def test_mobile_number_normalization():
    assert normalize_indian_mobile("+919876543210") == "+919876543210"
    assert normalize_indian_mobile("9876543210") == "+919876543210"
    assert normalize_indian_mobile("09876543210") == "+919876543210"
    assert normalize_indian_mobile("919876543210") == "+919876543210"
    # Invalid: non-Indian or non-10-digit
    assert normalize_indian_mobile("12345") is None
    assert normalize_indian_mobile("5551234567") is None  # Starts with 5 (invalid Indian mobile)


def test_account_deletion_flow(client):
    # Register user
    reg = client.post("/api/v1/auth/register", json={
        "email": "tobedeleted@example.com",
        "username": "tobedeleted",
        "password": "Password1234!",
        "consent_given": True
    })
    assert reg.status_code == 201
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Verify profile exists
    me = client.get("/api/v1/auth/me", headers=headers)
    assert me.status_code == 200

    # Delete account
    del_r = client.delete("/api/v1/auth/account", headers=headers)
    assert del_r.status_code == 200
    assert del_r.json()["status"] == "DELETED"

    # Profile lookup should now fail (account purged)
    me_after = client.get("/api/v1/auth/me", headers=headers)
    assert me_after.status_code == 401

