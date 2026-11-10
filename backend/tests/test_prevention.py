"""
test_prevention.py — Stage 6
Comprehensive test suite verifying:
  1. POST /api/v1/incidents (Create incident with auto-populated actions)
  2. GET /api/v1/incidents & GET /api/v1/incidents/{id}
  3. PATCH /api/v1/incidents/{id} (Update status & resolution notes)
  4. POST /api/v1/prevention/actions/{action_id}/complete
  5. POST /api/v1/prevention/recommendations (Dynamic threat recommendations)
  6. GET /api/v1/prevention/playbooks
  7. GET /api/v1/protection/overview
  8. POST /api/v1/assistant/security-guidance (OTP shared, Digital Arrest question, clicked link)
"""
import pytest
from fastapi.testclient import TestClient


def test_create_and_retrieve_incident(client: TestClient):
    """Verify incident creation auto-populates playbooks and can be fetched."""
    payload = {
        "category": "PHISHING",
        "title": "Phishing Link Clicked on SMS",
        "severity": "HIGH",
        "summary": "User clicked an urgent banking SMS link leading to fake HDFC portal.",
        "related_analysis_id": 101,
        "evidence_references": "http://secure-login-hdfcbank.serveo.net/login"
    }
    create_resp = client.post("/api/v1/incidents", json=payload)
    assert create_resp.status_code == 201
    data = create_resp.json()

    assert data["incident_number"].startswith("CR-INC-")
    assert data["category"] == "PHISHING"
    assert data["status"] == "ACTION_REQUIRED"
    assert len(data["actions"]) >= 2
    inc_id = data["id"]

    # Retrieve incident details
    get_resp = client.get(f"/api/v1/incidents/{inc_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == inc_id


def test_complete_incident_action(client: TestClient):
    """Verify completing an incident containment action updates state."""
    # 1. Create incident
    payload = {
        "category": "FINANCIAL_FRAUD",
        "title": "Unauthorized UPI Transfer",
        "severity": "CRITICAL",
        "summary": "Transferred Rs 15,000 under fake electricity bill disconnection notice."
    }
    create_resp = client.post("/api/v1/incidents", json=payload)
    assert create_resp.status_code == 201
    inc_data = create_resp.json()
    action = inc_data["actions"][0]
    action_id = action["id"]

    # 2. Mark action complete
    comp_resp = client.post(f"/api/v1/prevention/actions/{action_id}/complete")
    assert comp_resp.status_code == 200
    assert comp_resp.json()["is_completed"] is True
    assert comp_resp.json()["completed_at"] is not None


def test_update_incident_status(client: TestClient):
    """Verify updating incident status to RESOLVED."""
    payload = {
        "category": "SUSPICIOUS_COMMUNICATION",
        "title": "Suspicious WhatsApp Job Offer",
        "severity": "MEDIUM",
        "summary": "Received suspicious message promising daily payout for liking videos."
    }
    create_resp = client.post("/api/v1/incidents", json=payload)
    inc_id = create_resp.json()["id"]

    update_resp = client.patch(
        f"/api/v1/incidents/{inc_id}",
        json={"status": "RESOLVED", "resolution_notes": "Sender blocked, reported on Chakshu portal."}
    )
    assert update_resp.status_code == 200
    updated_data = update_resp.json()
    assert updated_data["status"] == "RESOLVED"
    assert updated_data["resolution_notes"] == "Sender blocked, reported on Chakshu portal."
    assert updated_data["resolved_at"] is not None


def test_prevention_recommendations_endpoint(client: TestClient):
    """Verify dynamic tailored recommendations generation."""
    payload = {
        "classification": "DIGITAL_ARREST_SCAM",
        "risk_level": "CRITICAL",
        "risk_score": 92.5,
        "threat_category": "Digital Arrest Extortion",
        "detected_indicators": ["Official Authority Impersonation", "Video Call Coercion"]
    }
    resp = client.post("/api/v1/prevention/recommendations", json=payload)
    assert resp.status_code == 200
    data = resp.json()

    assert len(data["immediate_actions"]) > 0
    assert any("disconnect" in act["title"].lower() or "terminate" in act["title"].lower() for act in data["immediate_actions"])
    assert any("1930" in rep["title"] for rep in data["reporting_guidance"])


def test_get_playbooks_endpoint(client: TestClient):
    """Verify listing available incident response playbooks."""
    resp = client.get("/api/v1/prevention/playbooks")
    assert resp.status_code == 200
    playbooks = resp.json()
    assert isinstance(playbooks, list)
    assert len(playbooks) >= 3
    ids = [pb["id"] for pb in playbooks]
    assert "PLAYBOOK_PHISHING_LINK" in ids
    assert "PLAYBOOK_DIGITAL_ARREST" in ids


def test_protection_overview_endpoint(client: TestClient):
    """Verify personal protection center overview metrics."""
    resp = client.get("/api/v1/protection/overview")
    assert resp.status_code == 200
    data = resp.json()
    assert "security_posture_score" in data
    assert "active_incidents_count" in data
    assert "available_playbooks_count" in data
    assert data["privacy_mode"] == "STRICT_LOCAL_ONLY"


def test_security_guidance_assistant(client: TestClient):
    """Verify AI Security Assistant provides factual guidance on critical queries."""
    # Query 1: Shared OTP
    resp_otp = client.post(
        "/api/v1/assistant/security-guidance",
        json={"query": "I accidentally shared my OTP with someone claiming to be from my bank. What should I do?"}
    )
    assert resp_otp.status_code == 200
    data_otp = resp_otp.json()
    assert data_otp["category"] == "ACCOUNT_COMPROMISE"
    assert len(data_otp["action_steps"]) >= 2
    assert any("1930" in res.get("contact", "") for res in data_otp["official_resources"])

    # Query 2: Digital Arrest threat
    resp_da = client.post(
        "/api/v1/assistant/security-guidance",
        json={"query": "A CBI officer is calling me on Skype saying I am under digital arrest."}
    )
    assert resp_da.status_code == 200
    data_da = resp_da.json()
    assert data_da["category"] == "DIGITAL_ARREST_EXTORTION"
    assert any("hang up" in step.lower() or "disconnect" in step.lower() for step in data_da["action_steps"])

