"""
Cyber Raksha AI - Phase B2 Automated Test Suite
Stage 17: Mobile Fraud Protection (SMS & Call Screening)
Tests: 28 comprehensive automated tests
"""
import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.database.session import get_db, SessionLocal, init_db
from app.models.device import Device

# Ensure tables exist
init_db()
from app.models.sms_analysis import SmsAnalysis
from app.models.phone_reputation import PhoneReputation
from app.models.threat_intel import ThreatIndicator
from app.models.notification import Notification
from app.services.phone_reputation_service import phone_reputation_service
from app.services.sms_analysis_service import sms_analysis_service


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="module")
def test_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="module", autouse=True)
def setup_mobile_test_environment(test_db: Session):
    """Seed test devices, threat indicators, and known bad numbers."""
    # Register test devices safely
    for dev_id, name in [
        ("mobile-test-device-uuid-0001", "Google Pixel 8 - Test Device A"),
        ("mobile-test-device-uuid-0002", "Samsung Galaxy S24 - Test Device B")
    ]:
        existing_dev = test_db.query(Device).filter(Device.device_id == dev_id).first()
        if not existing_dev:
            test_db.add(Device(
                device_id=dev_id,
                device_name=name,
                app_version="1.0.0",
                status="ACTIVE",
                security_posture="PROTECTED",
                registered_at=datetime.now(timezone.utc),
                last_seen_at=datetime.now(timezone.utc)
            ))

    # Known malicious threat indicator for URL cross-referencing
    ioc_val = "sbi-kyc-verify-portal.top"
    existing_ioc = test_db.query(ThreatIndicator).filter(ThreatIndicator.indicator_value == ioc_val).first()
    if not existing_ioc:
        test_db.add(ThreatIndicator(
            indicator_type="DOMAIN",
            indicator_value=ioc_val,
            threat_type="PHISHING",
            severity="CRITICAL",
            confidence_score=0.99,
            source_name="URLHAUS",
            description="Fake SBI NetBanking KYC harvest site",
            is_active=True,
            first_seen=datetime.now(timezone.utc),
            last_seen=datetime.now(timezone.utc),
            created_at=datetime.now(timezone.utc)
        ))

    # Known scam caller reputation
    rep_num = "+919876543210"
    existing_rep = test_db.query(PhoneReputation).filter(PhoneReputation.phone_number == rep_num).first()
    if not existing_rep:
        test_db.add(PhoneReputation(
            phone_number=rep_num,
            risk_level="CRITICAL",
            fraud_category="DIGITAL_ARREST",
            report_count=8,
            confidence_score=0.95,
            source="GOV_DATABASE",
            notes="Impersonating CBI Officer extorting money via video call",
            created_at=datetime.now(timezone.utc),
            last_reported_at=datetime.now(timezone.utc)
        ))

    test_db.commit()


# ==============================================================================
# SECTION 1: SMS FRAUD DETECTION (12 TESTS)
# ==============================================================================

def test_01_sms_banking_fraud_detection(client: TestClient):
    """Test 1: Detects fake bank account suspension and KYC phishing."""
    res = client.post(
        "/api/v1/mobile/analyze-message",
        json={
            "device_id": "mobile-test-device-uuid-0001",
            "message_text": "Dear Customer, your SBI account has been blocked today due to pending KYC update. Click http://sbi-kyc-verify-portal.top to avoid permanent suspension."
        }
    )
    assert res.status_code == 200
    data = res.json()
    assert data["risk_level"] in {"HIGH", "CRITICAL"}
    assert data["fraud_category"] == "BANKING_FRAUD"
    assert data["risk_score"] >= 60.0
    assert any("kyc" in r.lower() or "blocked" in r.lower() for r in data["detection_reasons"])


def test_02_sms_upi_fraud_detection(client: TestClient):
    """Test 2: Detects fraudulent collect requests and fake UPI refunds."""
    res = client.post(
        "/api/v1/mobile/analyze-message",
        json={
            "device_id": "mobile-test-device-uuid-0001",
            "message_text": "Congratulations! Paytm Cashback of Rs 4999 credited. Enter your UPI PIN to receive money in bank account immediately."
        }
    )
    assert res.status_code == 200
    data = res.json()
    assert data["risk_level"] in {"HIGH", "CRITICAL"}
    assert data["fraud_category"] == "UPI_FRAUD"
    assert any("upi" in r.lower() or "payment" in r.lower() for r in data["detection_reasons"])


def test_03_sms_otp_fraud_detection(client: TestClient):
    """Test 3: Detects explicit OTP harvest and authentication interception."""
    res = client.post(
        "/api/v1/mobile/analyze-message",
        json={
            "device_id": "mobile-test-device-uuid-0001",
            "message_text": "Urgent: share your OTP 849201 with bank executive to verify your debit card transaction or it will be declined."
        }
    )
    assert res.status_code == 200
    data = res.json()
    assert data["risk_level"] in {"HIGH", "CRITICAL"}
    assert data["fraud_category"] == "OTP_FRAUD"
    assert "DO NOT SHARE OTP" in data["recommended_action"]


def test_04_sms_delivery_scam_detection(client: TestClient):
    """Test 4: Detects fake courier package on hold with customs charge demand."""
    res = client.post(
        "/api/v1/mobile/analyze-message",
        json={
            "device_id": "mobile-test-device-uuid-0001",
            "message_text": "IndiaPost: Your parcel is on hold due to incorrect address. Pay delivery fee Rs 48 within 24 hours at http://indiapost-update.xyz/pay"
        }
    )
    assert res.status_code == 200
    data = res.json()
    assert data["risk_level"] in {"HIGH", "CRITICAL"}
    assert data["fraud_category"] == "DELIVERY_SCAM"


def test_05_sms_lottery_and_investment_scam(client: TestClient):
    """Test 5: Detects unsolicited lottery awards and guaranteed crypto returns."""
    res = client.post(
        "/api/v1/mobile/analyze-message",
        json={
            "device_id": "mobile-test-device-uuid-0001",
            "message_text": "You won lottery Rs 25,00,000 in KBC Lucky Draw! Contact Telegram task manager for guaranteed profit bonus."
        }
    )
    assert res.status_code == 200
    data = res.json()
    assert data["risk_level"] in {"HIGH", "CRITICAL"}
    assert data["fraud_category"] == "LOTTERY_SCAM"


def test_06_sms_gov_impersonation_digital_arrest(client: TestClient):
    """Test 6: Detects police/CBI intimidation and digital arrest threats."""
    res = client.post(
        "/api/v1/mobile/analyze-message",
        json={
            "device_id": "mobile-test-device-uuid-0001",
            "message_text": "CBI Notice: Digital arrest warrant issued by Cyber Crime Department for illegal parcel containing contraband. Do not leave home."
        }
    )
    assert res.status_code == 200
    data = res.json()
    assert data["risk_level"] == "CRITICAL"
    assert data["fraud_category"] == "GOV_IMPERSONATION"
    assert data["risk_score"] >= 80.0


def test_07_sms_benign_message(client: TestClient):
    """Test 7: Correctly identifies benign conversational message without false positives."""
    res = client.post(
        "/api/v1/mobile/analyze-message",
        json={
            "device_id": "mobile-test-device-uuid-0001",
            "message_text": "Hi Rahul, are we still meeting for lunch at 1 PM today? Let me know."
        }
    )
    assert res.status_code == 200
    data = res.json()
    assert data["risk_level"] in {"SAFE", "LOW"}
    assert data["fraud_category"] == "BENIGN"
    assert data["risk_score"] < 25.0


def test_08_sms_malicious_url_indicator_match(client: TestClient):
    """Test 8: Cross-references extracted URL with ThreatIndicator database."""
    res = client.post(
        "/api/v1/mobile/analyze-message",
        json={
            "device_id": "mobile-test-device-uuid-0001",
            "message_text": "Notice: update your credentials immediately at https://sbi-kyc-verify-portal.top/login"
        }
    )
    assert res.status_code == 200
    data = res.json()
    assert len(data["url_threats"]) >= 1
    threat = data["url_threats"][0]
    assert threat["is_malicious"] is True
    assert threat["threat_type"] == "PHISHING"
    assert threat["source"] == "URLHAUS"


def test_09_sms_url_shortener_heuristic(client: TestClient):
    """Test 9: Identifies obfuscated link using URL shortener service."""
    urls = sms_analysis_service.extract_urls("Click bit.ly/secure-gift to redeem")
    assert any("bit.ly" in u for u in urls)


def test_10_sms_urgency_and_credential_scoring(client: TestClient):
    """Test 10: Manufactured urgency and credential demands appropriately elevate score."""
    res = client.post(
        "/api/v1/mobile/analyze-message",
        json={
            "device_id": "mobile-test-device-uuid-0001",
            "message_text": "Immediate action required: enter your netbanking password within 10 minutes or face legal action."
        }
    )
    assert res.status_code == 200
    data = res.json()
    assert data["risk_score"] >= 50.0
    assert any("urgency" in r.lower() or "credential" in r.lower() for r in data["detection_reasons"])


def test_11_sms_sender_impersonation(client: TestClient):
    """Test 11: Official institution alert sent from personal 10-digit number adds risk penalty."""
    res = client.post(
        "/api/v1/mobile/analyze-message",
        json={
            "device_id": "mobile-test-device-uuid-0001",
            "message_text": "Your HDFC Bank account is blocked. Verify now.",
            "sender": "+919811223344"
        }
    )
    assert res.status_code == 200
    data = res.json()
    assert any("personal mobile" in r.lower() for r in data["detection_reasons"])


def test_12_sms_privacy_zero_retention_verification(client: TestClient, test_db: Session):
    """Test 12: Strict privacy guarantee - raw message text is never stored in DB, only SHA-256 hash."""
    secret_text = "Private secret message with personal details 998877"
    res = client.post(
        "/api/v1/mobile/analyze-message",
        json={
            "device_id": "mobile-test-device-uuid-0001",
            "message_text": secret_text
        }
    )
    assert res.status_code == 200
    msg_hash = res.json()["message_hash"]

    # Verify database record contains only the hash
    record = test_db.query(SmsAnalysis).filter(SmsAnalysis.message_hash == msg_hash).first()
    assert record is not None
    # Ensure there is no column on SmsAnalysis storing raw text
    assert not hasattr(record, "message_text")
    assert not hasattr(record, "raw_content")


# ==============================================================================
# SECTION 2: PHONE NUMBER REPUTATION (8 TESTS)
# ==============================================================================

def test_13_check_known_scam_number(client: TestClient):
    """Test 13: Correctly identifies known scammer and returns reputation data."""
    res = client.post(
        "/api/v1/mobile/check-number",
        json={
            "device_id": "mobile-test-device-uuid-0001",
            "phone_number": "+919876543210"
        }
    )
    assert res.status_code == 200
    data = res.json()
    assert data["risk_level"] == "CRITICAL"
    assert data["fraud_category"] == "DIGITAL_ARREST"
    assert data["report_count"] >= 8
    assert "Decline call" in data["recommended_action"]


def test_14_check_unlisted_number_returns_unknown(client: TestClient):
    """Test 14: Accurately returns UNKNOWN for unlisted numbers without fabricating data."""
    res = client.post(
        "/api/v1/mobile/check-number",
        json={
            "device_id": "mobile-test-device-uuid-0001",
            "phone_number": "+919999999999"
        }
    )
    assert res.status_code == 200
    data = res.json()
    assert data["risk_level"] == "UNKNOWN"
    assert data["confidence_score"] == 0.0
    assert data["report_count"] == 0


def test_15_number_normalization_10_digit_indian(client: TestClient):
    """Test 15: Standard 10-digit number normalizes to +91 international format."""
    normalized = phone_reputation_service.normalize_number("9876543210")
    assert normalized == "+919876543210"


def test_16_number_normalization_dashes_spaces_brackets(client: TestClient):
    """Test 16: Punctuation, dashes, parentheses and spaces stripped cleanly."""
    normalized = phone_reputation_service.normalize_number("(098) 765-43210")
    assert normalized == "+919876543210"


def test_17_number_normalization_international_preserved(client: TestClient):
    """Test 17: International numbers with '+' prefix are properly preserved."""
    normalized = phone_reputation_service.normalize_number("+1 (555) 234-5678")
    assert normalized == "+15552345678"


def test_18_report_phone_number_success(client: TestClient):
    """Test 18: User threat reporting creates a new community reputation record."""
    res = client.post(
        "/api/v1/mobile/report-threat",
        json={
            "device_id": "mobile-test-device-uuid-0001",
            "threat_type": "PHONE_NUMBER",
            "indicator_value": "+918800112233",
            "fraud_category": "UPI_SCAM",
            "description": "Caller requested UPI PIN for fake electricity bill payment"
        }
    )
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["report_id"] is not None


def test_19_repeated_reports_escalate_severity(client: TestClient, test_db: Session):
    """Test 19: Multiple community reports escalate risk level from MEDIUM to HIGH/CRITICAL."""
    # Submit 3 additional reports for the same number
    for i in range(3):
        phone_reputation_service.report_number(
            db=test_db,
            raw_number="+918800112233",
            fraud_category="UPI_SCAM",
            notes=f"Report {i+2}"
        )

    res = client.post(
        "/api/v1/mobile/check-number",
        json={
            "device_id": "mobile-test-device-uuid-0001",
            "phone_number": "+918800112233"
        }
    )
    assert res.status_code == 200
    data = res.json()
    assert data["risk_level"] in {"HIGH", "CRITICAL"}
    assert data["report_count"] >= 3


def test_20_actionable_recommendation_per_severity():
    """Test 20: Verified appropriate warning messages tailored to risk level."""
    rec_crit = phone_reputation_service._get_recommended_action("CRITICAL", "DIGITAL_ARREST")
    assert "Decline" in rec_crit

    rec_safe = phone_reputation_service._get_recommended_action("SAFE", None)
    assert "VERIFIED" in rec_safe


# ==============================================================================
# SECTION 3: MOBILE API & SECURITY ISOLATION (8 TESTS)
# ==============================================================================

def test_21_unregistered_device_rejected_on_analyze(client: TestClient):
    """Test 21: Rejects message analysis from unknown device with 404."""
    res = client.post(
        "/api/v1/mobile/analyze-message",
        json={
            "device_id": "unknown-nonexistent-device-uuid-9999",
            "message_text": "Sample text"
        }
    )
    assert res.status_code == 404
    assert "not registered" in res.json()["detail"]


def test_22_unregistered_device_rejected_on_check_number(client: TestClient):
    """Test 22: Rejects caller check from unknown device with 404."""
    res = client.post(
        "/api/v1/mobile/check-number",
        json={
            "device_id": "unknown-nonexistent-device-uuid-9999",
            "phone_number": "+919876543210"
        }
    )
    assert res.status_code == 404


def test_23_high_risk_sms_creates_system_notification(client: TestClient, test_db: Session):
    """Test 23: High/Critical SMS fraud triggers real-time Security Notification."""
    initial_count = test_db.query(Notification).count()

    res = client.post(
        "/api/v1/mobile/analyze-message",
        json={
            "device_id": "mobile-test-device-uuid-0001",
            "message_text": "URGENT CUSTOMS NOTICE: Contraband drugs intercepted at airport in your name. Digital arrest warrant issued. Transfer penalty immediately to avoid arrest.",
            "sender": "CUSTOMS_DELHI"
        }
    )
    assert res.status_code == 200

    new_count = test_db.query(Notification).count()
    assert new_count >= initial_count + 1


def test_24_threat_history_tenant_isolation(client: TestClient):
    """Test 24: Threat history returns items belonging strictly to requesting device."""
    # Analyze message for Device A
    client.post(
        "/api/v1/mobile/analyze-message",
        json={
            "device_id": "mobile-test-device-uuid-0001",
            "message_text": "KBC Lottery Winner Rs 50 Lakhs!"
        }
    )

    res = client.get(
        "/api/v1/mobile/threat-history",
        params={"device_id": "mobile-test-device-uuid-0001"}
    )
    assert res.status_code == 200
    data = res.json()
    assert data["device_id"] == "mobile-test-device-uuid-0001"
    assert data["total"] >= 1


def test_25_cross_device_data_leak_prevention(client: TestClient):
    """Test 25: Device B cannot observe or query threat history created on Device A."""
    res_b = client.get(
        "/api/v1/mobile/threat-history",
        params={"device_id": "mobile-test-device-uuid-0002"}
    )
    assert res_b.status_code == 200
    data_b = res_b.json()
    # Device B hasn't run any message analyses
    assert data_b["total"] == 0
    assert len(data_b["items"]) == 0


def test_26_mobile_protection_status_endpoint(client: TestClient):
    """Test 26: Returns capability health, active modules, and signature counts."""
    res = client.get(
        "/api/v1/mobile/protection-status",
        params={"device_id": "mobile-test-device-uuid-0001"}
    )
    assert res.status_code == 200
    data = res.json()
    assert data["sms_protection"] == "ACTIVE"
    assert data["call_protection"] == "ACTIVE"
    assert data["database_signatures_count"] >= 1
    assert data["phone_reputation_entries"] >= 1


def test_27_report_threat_url_ingestion(client: TestClient, test_db: Session):
    """Test 27: Reporting a malicious URL updates threat indicator repository."""
    res = client.post(
        "/api/v1/mobile/report-threat",
        json={
            "device_id": "mobile-test-device-uuid-0001",
            "threat_type": "MALICIOUS_URL",
            "indicator_value": "https://fake-bank-auth-token.xyz",
            "fraud_category": "CREDENTIAL_THEFT",
            "description": "Phishing portal reported by mobile user"
        }
    )
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True

    # Verify indicator in DB
    ind = test_db.query(ThreatIndicator).filter(ThreatIndicator.indicator_value == "https://fake-bank-auth-token.xyz").first()
    assert ind is not None
    assert ind.threat_type == "CREDENTIAL_THEFT"


def test_28_request_validation_rejection(client: TestClient):
    """Test 28: Empty message or invalid threat type triggers 422 Unprocessable Entity."""
    # Empty message
    res1 = client.post(
        "/api/v1/mobile/analyze-message",
        json={
            "device_id": "mobile-test-device-uuid-0001",
            "message_text": "   "
        }
    )
    assert res1.status_code == 422

    # Invalid threat type
    res2 = client.post(
        "/api/v1/mobile/report-threat",
        json={
            "device_id": "mobile-test-device-uuid-0001",
            "threat_type": "INVALID_TYPE",
            "indicator_value": "12345"
        }
    )
    assert res2.status_code == 422
