"""
Cyber Raksha AI - Comprehensive Master Integration Tests
Tests: User Auth, Mobile OTP, Email Verification, Cybercrime Complaint Assistant, Community Intelligence.
"""
import pytest


def test_user_registration_and_login(client):
    reg_payload = {
        "email": "testcitizen@example.com",
        "username": "testcitizen",
        "password": "SecurePassword123!",
        "full_name": "Test Citizen",
        "mobile_number": "9876543210",
        "consent_given": True
    }
    r = client.post("/api/v1/auth/register", json=reg_payload)
    assert r.status_code == 201
    data = r.json()
    assert data["username"] == "testcitizen"
    assert data["email"] == "testcitizen@example.com"
    assert data["mobile_number"] == "+919876543210"
    assert "access_token" in data

    # Test login with email
    login_r = client.post("/api/v1/auth/login", json={
        "identifier": "testcitizen@example.com",
        "password": "SecurePassword123!"
    })
    assert login_r.status_code == 200
    token = login_r.json()["access_token"]
    assert token is not None

    # Test login with mobile
    login_m = client.post("/api/v1/auth/login", json={
        "identifier": "9876543210",
        "password": "SecurePassword123!"
    })
    assert login_m.status_code == 200

    # Test /me endpoint
    headers = {"Authorization": f"Bearer {token}"}
    me_r = client.get("/api/v1/auth/me", headers=headers)
    assert me_r.status_code == 200
    me_data = me_r.json()
    assert me_data["username"] == "testcitizen"
    assert me_data["consent_given"] is True


def test_mobile_otp_flow(client):
    # Login as citizen
    login_r = client.post("/api/v1/auth/login", json={
        "identifier": "testcitizen@example.com",
        "password": "SecurePassword123!"
    })
    token = login_r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Request OTP
    otp_req = client.post("/api/v1/auth/send-mobile-otp", json={"mobile_number": "9876543210"}, headers=headers)
    assert otp_req.status_code == 200
    assert otp_req.json()["status"] == "SUCCESS"

    # From DB or service, check OTP verification with wrong code
    bad_verify = client.post("/api/v1/auth/verify-mobile-otp", json={"otp": "000000"}, headers=headers)
    assert bad_verify.status_code == 400
    assert "Incorrect OTP" in bad_verify.json()["detail"]


def test_complaint_assistant_flow(client):
    # Login to get token
    login_r = client.post("/api/v1/auth/login", json={
        "identifier": "testcitizen@example.com",
        "password": "SecurePassword123!"
    })
    token = login_r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Draft complaint
    draft_payload = {
        "complaint_category": "BANKING_FRAUD",
        "suspect_identifier": "+919812345678",
        "financial_loss_inr": 25000.0,
        "description": "Victim received an urgent SMS claiming account suspension and was deceived into sharing OTP.",
        "evidence_summary": "Test evidence: Raw SMS message with fraudulent link."
    }
    draft_r = client.post("/api/v1/complaints/draft", json=draft_payload, headers=headers)
    assert draft_r.status_code == 201
    c_data = draft_r.json()
    cid = c_data["complaint_id"]
    assert cid.startswith("CR-CMP-")
    assert c_data["helpline_number"] == "1930"
    assert c_data["official_portal_url"] == "https://cybercrime.gov.in"
    assert c_data["status"] == "DRAFT"

    # 2. Record official acknowledgement number from cybercrime.gov.in
    ack_payload = {
        "official_ack_number": "ACK-2026-IN-987654",
        "notes": "Filed on cybercrime.gov.in citizen portal under incident 1930 reference."
    }
    ack_r = client.post(f"/api/v1/complaints/{cid}/ack", json=ack_payload, headers=headers)
    assert ack_r.status_code == 200
    ack_data = ack_r.json()
    assert ack_data["status"] == "OFFICIALLY_SUBMITTED"
    assert ack_data["official_ack_number"] == "ACK-2026-IN-987654"

    # 3. List complaints
    list_r = client.get("/api/v1/complaints", headers=headers)
    assert list_r.status_code == 200
    all_c = list_r.json()
    assert len(all_c) >= 1
    assert any(c["complaint_id"] == cid for c in all_c)


def test_community_threat_reporting_and_reputation(client):
    indicator = "+919999888877"
    report_payload = {
        "indicator": indicator,
        "indicator_type": "PHONE",
        "category": "DIGITAL_ARREST",
        "description": "Suspect called impersonating CBI officer demanding video KYC.",
        "severity": "CRITICAL"
    }

    # Submit report 1
    r1 = client.post("/api/v1/community/report", json=report_payload)
    assert r1.status_code == 201
    assert r1.json()["total_reports"] == 1

    # Check initial reputation
    rep_r = client.get(f"/api/v1/community/reputation/{indicator}")
    assert rep_r.status_code == 200
    rep_data = rep_r.json()
    assert rep_data["total_reports"] == 1
    assert rep_data["reputation_status"] in ("REPORTED", "SUSPICIOUS")

    # Submit 2 more reports to escalate to threshold
    client.post("/api/v1/community/report", json=report_payload)
    client.post("/api/v1/community/report", json=report_payload)

    # Re-check reputation
    rep_r3 = client.get(f"/api/v1/community/reputation/{indicator}")
    assert rep_r3.status_code == 200
    data3 = rep_r3.json()
    assert data3["total_reports"] == 3
    assert data3["is_malicious"] is True
    assert data3["risk_score"] >= 75.0
