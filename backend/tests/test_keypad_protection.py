"""
Cyber Raksha AI - Test Suite for Keypad User Protection System
Covers all 20 required verification scenarios:
1. Family registration
2. Invalid family registration
3. Missing consent rejection (422)
4. Unauthorized family access (401)
5. SMS digital arrest analysis
6. Electricity scam analysis
7. Bank KYC scam analysis
8. Legitimate SMS analysis
9. Unknown call number
10. Reported scam number
11. Repeated scam reporting (de-duplication)
12. False-report resistance (Anti-Sybil guard)
13. Guardian incident creation
14. Incident acknowledgment
15. Cross-guardian incident isolation
16. Kannada education
17. Hindi education
18. English education
19. Helpdesk response & legal distinction
20. Invalid input handling
"""
import pytest
from app.models.user import User
from app.core.auth_utils import create_access_token


@pytest.fixture
def test_guardians(db_session):
    """Creates two distinct active guardians for authentication & cross-guardian tests."""
    # Guardian A (Alice)
    u_a = db_session.query(User).filter(User.username == "test_guardian_alice").first()
    if not u_a:
        u_a = User(
            username="test_guardian_alice",
            email="alice@guardian.test",
            hashed_password="not_used_test_pw",
            role="USER",
            is_active=True
        )
        db_session.add(u_a)
        db_session.commit()
        db_session.refresh(u_a)

    token_a = create_access_token({"sub": u_a.id})
    headers_a = {"Authorization": f"Bearer {token_a}"}

    # Guardian B (Bob)
    u_b = db_session.query(User).filter(User.username == "test_guardian_bob").first()
    if not u_b:
        u_b = User(
            username="test_guardian_bob",
            email="bob@guardian.test",
            hashed_password="not_used_test_pw",
            role="USER",
            is_active=True
        )
        db_session.add(u_b)
        db_session.commit()
        db_session.refresh(u_b)

    token_b = create_access_token({"sub": u_b.id})
    headers_b = {"Authorization": f"Bearer {token_b}"}

    return {
        "user_a": u_a,
        "headers_a": headers_a,
        "user_b": u_b,
        "headers_b": headers_b
    }


# ── 1. Family Registration ───────────────────────────────────────────────────

def test_01_family_registration(client, test_guardians):
    """TC-01: Valid family registration returns 201 with E.164 normalization & privacy masking."""
    payload = {
        "full_name": "Ramesh Kumar",
        "mobile_number": "9845012345",
        "relationship": "Father",
        "device_type": "Nokia 105",
        "preferred_language": "hi",
        "consent_given": True,
        "consent_notes": "Verbal consent given."
    }
    r = client.post("/api/v1/keypad/family", json=payload, headers=test_guardians["headers_a"])
    assert r.status_code == 201
    data = r.json()
    assert data["full_name"] == "Ramesh Kumar"
    assert data["mobile_number"] == "+919845012345"
    assert data["masked_mobile_number"].startswith("+91")
    assert data["masked_mobile_number"].endswith("2345")
    assert data["guardian_user_id"] == test_guardians["user_a"].id


# ── 2. Invalid Family Registration ───────────────────────────────────────────

def test_02_invalid_family_registration_phone(client, test_guardians):
    """TC-02: Phone number with fewer than 10 digits is rejected with 422."""
    payload = {
        "full_name": "Invalid Phone User",
        "mobile_number": "12345",  # Too short
        "relationship": "Mother",
        "consent_given": True
    }
    r = client.post("/api/v1/keypad/family", json=payload, headers=test_guardians["headers_a"])
    assert r.status_code == 422


# ── 3. Missing Consent Rejection ─────────────────────────────────────────────

def test_03_missing_consent_rejection(client, test_guardians):
    """TC-03: Registering without consent is rejected with 422."""
    payload = {
        "full_name": "No Consent Dependent",
        "mobile_number": "9845099999",
        "relationship": "Grandmother",
        "consent_given": False
    }
    r = client.post("/api/v1/keypad/family", json=payload, headers=test_guardians["headers_a"])
    assert r.status_code == 422


# ── 4. Unauthorized Family Access ────────────────────────────────────────────

def test_04_unauthorized_family_access(client):
    """TC-04: Endpoints require JWT authentication; anonymous requests return 401."""
    r_list = client.get("/api/v1/keypad/family")
    assert r_list.status_code == 401

    r_post = client.post("/api/v1/keypad/family", json={"full_name": "Anon", "mobile_number": "9845012345"})
    assert r_post.status_code == 401

    r_alerts = client.get("/api/v1/keypad/alerts")
    assert r_alerts.status_code == 401


# ── 5. SMS Digital Arrest Analysis ───────────────────────────────────────────

def test_05_sms_digital_arrest_analysis(client, test_guardians):
    """TC-05: Digital arrest scam text triggers CRITICAL/HIGH risk category."""
    req = {
        "sender": "+919988776655",
        "message": "CBI POLICE NOTICE: An arrest warrant has been issued in your name for narcotics package. You are placed under digital arrest. Call officer immediately.",
        "preferred_language": "en"
    }
    r = client.post("/api/v1/keypad/check-sms", json=req, headers=test_guardians["headers_a"])
    assert r.status_code == 200
    data = r.json()
    assert data["risk_level"] in ("HIGH", "CRITICAL")
    assert data["category"] == "DIGITAL_ARREST"
    assert data["is_automatic_detection"] is False
    assert "disclaimer" in data


# ── 6. Electricity Scam Analysis ─────────────────────────────────────────────

def test_06_electricity_scam_analysis(client, test_guardians):
    """TC-06: Electricity disconnection SMS detected with category ELECTRICITY_BILL."""
    req = {
        "sender": "VK-BESCOM",
        "message": "Dear Consumer, your electricity power will be disconnected tonight at 9:30 PM due to pending bill. Immediately call electricity officer at 9876543210.",
        "preferred_language": "hi"
    }
    r = client.post("/api/v1/keypad/check-sms", json=req, headers=test_guardians["headers_a"])
    assert r.status_code == 200
    data = r.json()
    assert data["category"] == "ELECTRICITY_BILL"
    assert data["risk_score"] >= 35.0


# ── 7. Bank KYC Scam Analysis ────────────────────────────────────────────────

def test_07_bank_kyc_scam_analysis(client, test_guardians):
    """TC-07: Bank KYC deactivation SMS detected with category BANK_KYC."""
    req = {
        "sender": "VM-SBIINB",
        "message": "Dear customer, your SBI bank account has been suspended due to expired KYC. Click http://bit.ly/sbi-kyc-fix to update immediately.",
        "preferred_language": "en"
    }
    r = client.post("/api/v1/keypad/check-sms", json=req, headers=test_guardians["headers_a"])
    assert r.status_code == 200
    data = r.json()
    assert data["category"] == "BANK_KYC"
    assert "UNVERIFIED_URL_PRESENT" in str(data["matched_signatures"])


# ── 8. Legitimate SMS Analysis ───────────────────────────────────────────────

def test_08_legitimate_sms_analysis(client, test_guardians):
    """TC-08: Benign postal delivery SMS evaluates to SAFE with 0.0 risk."""
    req = {
        "sender": "AD-INDPOST",
        "message": "Your speed post parcel EM123456789IN was delivered today at 2:15 PM.",
        "preferred_language": "en"
    }
    r = client.post("/api/v1/keypad/check-sms", json=req, headers=test_guardians["headers_a"])
    assert r.status_code == 200
    data = r.json()
    assert data["risk_level"] == "SAFE"
    assert data["risk_score"] == 0.0


# ── 9. Unknown Call Number ───────────────────────────────────────────────────

def test_09_unknown_call_number(client, test_guardians):
    """TC-09: Unreported number returns risk_level UNKNOWN and verification_status NO_REPORTS."""
    req = {"phone_number": "919999000001"}
    r = client.post("/api/v1/keypad/check-call", json=req, headers=test_guardians["headers_a"])
    assert r.status_code == 200
    data = r.json()
    assert data["risk_level"] == "UNKNOWN"
    assert data["verification_status"] == "NO_REPORTS"
    assert data["report_count"] == 0
    assert data["is_automatic_blocking"] is False


# ── 10. Reported Scam Number ─────────────────────────────────────────────────

def test_10_reported_scam_number(client, test_guardians):
    """TC-10: Number reported by guardian returns COMMUNITY_UNVERIFIED and report_count 1."""
    num = "919999000002"
    rep_req = {
        "phone_number": num,
        "fraud_category": "DIGITAL_ARREST",
        "claimed_caller_identity": "Fake Police Inspector",
        "evidence_notes": "Demanded money over phone call."
    }
    r_rep = client.post("/api/v1/keypad/report-scam", json=rep_req, headers=test_guardians["headers_a"])
    assert r_rep.status_code == 201

    r_check = client.post("/api/v1/keypad/check-call", json={"phone_number": num}, headers=test_guardians["headers_a"])
    assert r_check.status_code == 200
    data = r_check.json()
    assert data["verification_status"] == "COMMUNITY_UNVERIFIED"
    assert data["report_count"] == 1
    assert data["risk_level"] == "MEDIUM"


# ── 11. Repeated Scam Reporting (De-duplication) ─────────────────────────────

def test_11_repeated_scam_reporting_deduplication(client, test_guardians):
    """TC-11: Same guardian reporting the same number multiple times updates record without inflating report_count."""
    num = "919999000003"
    rep_req = {
        "phone_number": num,
        "fraud_category": "ELECTRICITY_BILL",
        "claimed_caller_identity": "BESCOM Officer"
    }
    # Report 1
    r1 = client.post("/api/v1/keypad/report-scam", json=rep_req, headers=test_guardians["headers_a"])
    assert r1.status_code == 201

    # Report 2 (same guardian)
    r2 = client.post("/api/v1/keypad/report-scam", json=rep_req, headers=test_guardians["headers_a"])
    assert r2.status_code == 201

    # Verify report_count remains 1 (de-duplicated)
    r_check = client.post("/api/v1/keypad/check-call", json={"phone_number": num}, headers=test_guardians["headers_a"])
    data = r_check.json()
    assert data["report_count"] == 1
    assert data["verification_status"] == "COMMUNITY_UNVERIFIED"


# ── 12. False-Report Resistance (Anti-Sybil Guard) ───────────────────────────

def test_12_false_report_resistance(client, test_guardians):
    """TC-12: Requires distinct guardians to escalate to CORROBORATED."""
    num = "919999000004"
    rep_req = {
        "phone_number": num,
        "fraud_category": "BANK_KYC"
    }

    # Guardian A reports -> 1 unique reporter (MEDIUM)
    client.post("/api/v1/keypad/report-scam", json=rep_req, headers=test_guardians["headers_a"])
    c1 = client.post("/api/v1/keypad/check-call", json={"phone_number": num}, headers=test_guardians["headers_a"]).json()
    assert c1["verification_status"] == "COMMUNITY_UNVERIFIED"
    assert c1["risk_level"] == "MEDIUM"

    # Guardian B reports -> 2 distinct reporters (CORROBORATED)
    client.post("/api/v1/keypad/report-scam", json=rep_req, headers=test_guardians["headers_b"])
    c2 = client.post("/api/v1/keypad/check-call", json={"phone_number": num}, headers=test_guardians["headers_b"]).json()
    assert c2["verification_status"] == "CORROBORATED"
    assert c2["report_count"] == 2


# ── 13. Guardian Incident Creation ───────────────────────────────────────────

def test_13_guardian_incident_creation(client, test_guardians):
    """TC-13: Suspicious SMS check automatically creates an incident in guardian alerts."""
    r_before = client.get("/api/v1/keypad/alerts", headers=test_guardians["headers_a"]).json()
    initial_count = r_before["total_incidents"]

    sms_req = {
        "message": "URGENT: Electricity disconnected at 9:30 PM tonight. Call BESCOM officer immediately at 9876543210.",
        "preferred_language": "en"
    }
    client.post("/api/v1/keypad/check-sms", json=sms_req, headers=test_guardians["headers_a"])

    r_after = client.get("/api/v1/keypad/alerts", headers=test_guardians["headers_a"]).json()
    assert r_after["total_incidents"] > initial_count
    assert len(r_after["recent_incidents"]) > 0


# ── 14. Incident Acknowledgment ──────────────────────────────────────────────

def test_14_incident_acknowledgment(client, test_guardians):
    """TC-14: Guardian can acknowledge an incident record."""
    r_alerts = client.get("/api/v1/keypad/alerts", headers=test_guardians["headers_a"]).json()
    unack_incidents = [i for i in r_alerts["recent_incidents"] if not i["is_acknowledged"]]
    assert len(unack_incidents) > 0

    target_id = unack_incidents[0]["id"]
    r_ack = client.post(f"/api/v1/keypad/alerts/{target_id}/acknowledge", headers=test_guardians["headers_a"])
    assert r_ack.status_code == 200
    assert r_ack.json()["status"] == "success"


# ── 15. Cross-Guardian Incident Isolation ────────────────────────────────────

def test_15_cross_guardian_incident_isolation(client, test_guardians):
    """TC-15: Guardian B cannot acknowledge or access Guardian A's incident."""
    # Guardian A has incidents
    r_a = client.get("/api/v1/keypad/alerts", headers=test_guardians["headers_a"]).json()
    assert len(r_a["recent_incidents"]) > 0
    inc_a_id = r_a["recent_incidents"][0]["id"]

    # Guardian B attempts to acknowledge Guardian A's incident -> 404
    r_b_ack = client.post(f"/api/v1/keypad/alerts/{inc_a_id}/acknowledge", headers=test_guardians["headers_b"])
    assert r_b_ack.status_code == 404


# ── 16. Kannada Education ────────────────────────────────────────────────────

def test_16_kannada_education(client):
    """TC-16: Returns complete Kannada fraud education with Golden Rule and 5 scam cards."""
    r = client.get("/api/v1/keypad/education?lang=kn")
    assert r.status_code == 200
    data = r.json()
    assert data["language"] == "kn"
    assert "ಸುವರ್ಣ ನಿಯಮ" in data["golden_rule_title"]
    assert len(data["common_scams"]) == 5
    assert len(data["do_not_share_items"]) >= 4


# ── 17. Hindi Education ──────────────────────────────────────────────────────

def test_17_hindi_education(client):
    """TC-17: Returns complete Hindi fraud education with Golden Rule and 5 scam cards."""
    r = client.get("/api/v1/keypad/education?lang=hi")
    assert r.status_code == 200
    data = r.json()
    assert data["language"] == "hi"
    assert "स्वर्ण नियम" in data["golden_rule_title"]
    assert len(data["common_scams"]) == 5


# ── 18. English Education ────────────────────────────────────────────────────

def test_18_english_education(client):
    """TC-18: Returns complete English fraud education with Golden Rule and 5 scam cards."""
    r = client.get("/api/v1/keypad/education?lang=en")
    assert r.status_code == 200
    data = r.json()
    assert data["language"] == "en"
    assert "GOLDEN RULE" in data["golden_rule_title"]
    assert len(data["common_scams"]) == 5


# ── 19. Helpdesk Response ────────────────────────────────────────────────────

def test_19_helpdesk_response(client):
    """TC-19: Returns official Sanchar Saathi Chakshu, 1930, 1909 and legal distinction."""
    r = client.get("/api/v1/keypad/helpdesks")
    assert r.status_code == 200
    data = r.json()
    portals = [p["name"] for p in data["portals"]]
    assert any("Chakshu" in p for p in portals)
    helplines = [h["contact_or_url"] for h in data["helplines"]]
    assert "1930" in helplines
    assert "1909" in helplines
    assert "112" in helplines
    assert "legal_clarification" in data


# ── 20. Invalid Input Handling ───────────────────────────────────────────────

def test_20_invalid_input_handling(client, test_guardians):
    """TC-20: Empty message or invalid short phone number returns 422."""
    # Empty SMS text
    r_sms = client.post("/api/v1/keypad/check-sms", json={"message": "   "}, headers=test_guardians["headers_a"])
    assert r_sms.status_code == 422

    # Malformed call phone number (less than 7 chars)
    r_call = client.post("/api/v1/keypad/check-call", json={"phone_number": "123"}, headers=test_guardians["headers_a"])
    assert r_call.status_code == 422
