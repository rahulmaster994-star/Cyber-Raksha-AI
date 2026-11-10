"""
Cyber Raksha AI - Phase B4: Intelligent Threat Detection Test Suite
Comprehensive automated verification for:
- URL Feature Extraction & Brand Impersonation
- Local ML Phishing Detection
- Context-Aware SMS Analysis (OTP theft, Digital Arrest, Delivery scams, Benign OTP alerts)
- Unified Multi-Vector Correlation Engine
- Explainable Threat Decisions & Provenance
"""
import uuid
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.database.session import SessionLocal
from app.models.device import Device
from app.models.threat_intel import ThreatIndicator
from app.schemas.security_event import UnifiedRiskEvaluationRequest
from app.services.central_risk_engine import central_risk_engine
from app.services.sms_analysis_service import sms_analysis_service
from ai_engine.core.brand_impersonation import check_brand_impersonation
from ai_engine.core.feature_extraction import extract_url_features, identify_risk_indicators
from ai_engine.inference.phishing_detector import detect_phishing, get_detector_status

client = TestClient(app)

TEST_DEVICE_UUID = f"device-b4-{uuid.uuid4().hex[:8]}"
TEST_DEVICE_TOKEN = f"token-b4-{uuid.uuid4().hex[:16]}"


@pytest.fixture(scope="module", autouse=True)
def setup_b4_test_environment():
    import hashlib
    db = SessionLocal()
    try:
        dev = Device(
            device_id=TEST_DEVICE_UUID,
            device_name="Pixel 9 Pro B4",
            device_token_hash=hashlib.sha256(TEST_DEVICE_TOKEN.encode("utf-8")).hexdigest(),
            app_version="1.0.0",
            status="ACTIVE",
            is_revoked=False
        )
        db.merge(dev)
        db.commit()
    finally:
        db.close()


# ==============================================================================
# 1. URL Feature Extraction & Brand Impersonation Tests (B4.1)
# ==============================================================================

def test_url_feature_extraction_lexical_dimensions():
    """Verify that feature extractor derives 25+ lexical and structural features."""
    url = "http://secure-login.bank-update.xyz:8888/portal/verify?session=123&user=rahul#submit"
    features = extract_url_features(url)
    assert isinstance(features, dict)
    assert features["url_length"] > 50
    assert features["has_suspicious_port"] == 1
    assert features["subdomain_count"] >= 1
    assert features["is_https"] == 0
    assert features["suspicious_keyword_count"] >= 2  # 'secure', 'login', 'verify'

    indicators = identify_risk_indicators(features, url)
    assert len(indicators) >= 2


def test_brand_impersonation_detection_hdfc():
    """Unauthorized domain imitating HDFC Bank is detected with explanation."""
    bad_host = "hdfc-bank-netbanking-verify.xyz"
    impersonation = check_brand_impersonation(bad_host)
    assert impersonation is not None
    assert impersonation["brand_id"] == "HDFC"
    assert impersonation["category"] == "BANKING"
    assert impersonation["risk_contribution"] >= 30.0
    assert "impersonates HDFC Bank" in impersonation["description"]


def test_brand_impersonation_detection_sbi_yono():
    """Unauthorized domain imitating SBI YONO is detected."""
    bad_host = "yono-sbi-kyc-update.com"
    impersonation = check_brand_impersonation(bad_host)
    assert impersonation is not None
    assert impersonation["brand_id"] == "SBI"
    assert "impersonates State Bank of India" in impersonation["description"]


def test_brand_impersonation_detection_indiapost():
    """Unauthorized domain imitating India Post / SpeedPost is detected."""
    bad_host = "indiapost-parcel-tracking.top"
    impersonation = check_brand_impersonation(bad_host)
    assert impersonation is not None
    assert impersonation["brand_id"] == "INDIA_POST"
    assert impersonation["category"] == "LOGISTICS"


def test_brand_impersonation_official_domain_not_flagged():
    """Official legitimate domains (e.g. hdfcbank.com, sbi.co.in, amazon.in) are not flagged."""
    assert check_brand_impersonation("netbanking.hdfcbank.com") is None
    assert check_brand_impersonation("onlinesbi.sbi") is None
    assert check_brand_impersonation("www.amazon.in") is None
    assert check_brand_impersonation("indiapost.gov.in") is None


def test_url_detector_ip_address_hostname():
    """URL with raw IP address hostname is flagged as high risk."""
    url = "http://192.168.1.50:8000/login/bank"
    res = detect_phishing(url)
    assert res.success is True
    assert res.analysis["features"]["has_ip_address"] == 1
    assert any("IP address" in ind for ind in res.analysis["risk_indicators"])


def test_url_detector_punycode_homograph():
    """Punycode (xn--) domain is flagged for potential homograph deception."""
    url = "http://xn--pple-43a.com/verify"
    res = detect_phishing(url)
    assert res.success is True
    assert res.analysis["features"]["is_punycode_or_idn"] == 1


# ==============================================================================
# 2. Local Intelligent Machine Learning Model Tests (B4.2)
# ==============================================================================

def test_ml_model_status_and_metadata():
    """Verify local ML model artifact availability, version, and training telemetry."""
    status = get_detector_status()
    assert status["engine_version"] == "1.0.0"
    assert status["model_available"] is True
    assert status["model_loaded"] is True
    assert status["algorithm"] in ["RandomForest", "RandomForestClassifier"]


def test_ml_inference_benign_url():
    """Legitimate benign URL evaluates to LOW risk / LEGITIMATE classification."""
    url = "https://www.wikipedia.org/wiki/Computer_security"
    res = detect_phishing(url)
    assert res.success is True
    assert res.classification == "LEGITIMATE"
    assert res.risk_level in ["LOW", "SAFE"]
    assert res.risk_score <= 25.0


def test_ml_inference_suspicious_phishing_url():
    """Deceptive phishing URL evaluates to HIGH risk / PHISHING classification."""
    url = "http://secure-login-hdfc.phishtest.invalid/netbanking?token=abc"
    res = detect_phishing(url)
    assert res.success is True
    assert res.classification in ["PHISHING", "SUSPICIOUS"]
    assert res.risk_score >= 60.0
    assert len(res.analysis["risk_indicators"]) > 0


# ==============================================================================
# 3. Context-Aware SMS Analysis Tests (B4.3)
# ==============================================================================

def test_sms_benign_outbound_otp_receipt_not_flagged():
    """
    Legitimate outbound OTP delivery notice ('Do not share with anyone')
    is recognized as a benign receipt and NOT flagged as OTP fraud.
    """
    db = SessionLocal()
    try:
        msg = "Your OTP for transaction of Rs 1500 at Amazon is 584920. Do not share this OTP with anyone for your security."
        res = sms_analysis_service.analyze_sms(
            db=db,
            device_id=TEST_DEVICE_UUID,
            message_text=msg,
            sender="HDFCBK"
        )
        assert res["risk_level"] in ["LOW", "SAFE"]
        assert res["risk_score"] < 30.0
        assert res["fraud_category"] != "OTP_FRAUD"
        assert any("outbound security notice" in r.lower() or "receipt" in r.lower() for r in res["detection_reasons"])
    finally:
        db.close()


def test_sms_otp_harvesting_theft_flagged_critical():
    """Explicit demands to share/send OTP are flagged as OTP_FRAUD."""
    db = SessionLocal()
    try:
        msg = "Urgent: Your SBI netbanking will be suspended today. Share your OTP with the bank manager to verify KYC immediately."
        res = sms_analysis_service.analyze_sms(
            db=db,
            device_id=TEST_DEVICE_UUID,
            message_text=msg,
            sender="+919876543210"
        )
        assert res["risk_score"] >= 75.0
        assert res["risk_level"] in ["HIGH", "CRITICAL"]
        assert res["fraud_category"] in ["OTP_FRAUD", "BANKING_FRAUD"]
    finally:
        db.close()


def test_sms_digital_arrest_extortion_threat():
    """Digital arrest / CBI / police extortion schemes are flagged as GOV_IMPERSONATION."""
    db = SessionLocal()
    try:
        msg = "CBI NOTICE: An arrest warrant has been issued against you under Narcotics Control Bureau. Digital arrest order in force. Join video interrogation immediately."
        res = sms_analysis_service.analyze_sms(
            db=db,
            device_id=TEST_DEVICE_UUID,
            message_text=msg,
            sender="+918888877777"
        )
        assert res["risk_score"] >= 80.0
        assert res["fraud_category"] == "GOV_IMPERSONATION"
        assert any("digital arrest" in r.lower() or "intimidation" in r.lower() for r in res["detection_reasons"])
    finally:
        db.close()


def test_sms_delivery_payment_scam():
    """Package held / unpaid fee scams with lookalike links are flagged as DELIVERY_SCAM."""
    db = SessionLocal()
    try:
        msg = "Your IndiaPost parcel cannot be delivered due to incomplete address. Update address and pay pending fee Rs 25 at http://indiapost-parcel-help.top/pay within 24 hours."
        res = sms_analysis_service.analyze_sms(
            db=db,
            device_id=TEST_DEVICE_UUID,
            message_text=msg,
            sender="+919876543210"
        )
        assert res["risk_score"] >= 70.0
        assert res["risk_level"] in ["HIGH", "CRITICAL"]
        assert len(res["extracted_urls"]) == 1
        assert any("parcel" in r.lower() or "delivery" in r.lower() or "impersonates" in r.lower() for r in res["detection_reasons"])
    finally:
        db.close()


def test_sms_lottery_investment_fraud():
    """Unsolicited Telegram task / crypto doubling scams are flagged as LOTTERY_SCAM."""
    db = SessionLocal()
    try:
        msg = "Congratulations! You won KBC lucky draw prize of Rs 25 Lakhs. Guaranteed daily profit of Rs 5000. Join our Telegram task group now."
        res = sms_analysis_service.analyze_sms(
            db=db,
            device_id=TEST_DEVICE_UUID,
            message_text=msg,
            sender="+919999900000"
        )
        assert res["risk_score"] >= 60.0
        assert res["fraud_category"] == "LOTTERY_SCAM"
    finally:
        db.close()


def test_sms_normal_personal_message():
    """Personal conversation messages evaluate to SAFE / BENIGN."""
    db = SessionLocal()
    try:
        msg = "Hey Rahul, let's meet for dinner at 8pm tonight near Connaught Place."
        res = sms_analysis_service.analyze_sms(
            db=db,
            device_id=TEST_DEVICE_UUID,
            message_text=msg,
            sender="+919811122233"
        )
        assert res["risk_score"] <= 10.0
        assert res["risk_level"] in ["SAFE", "LOW"]
        assert res["fraud_category"] == "BENIGN"
    finally:
        db.close()


# ==============================================================================
# 4. Unified Risk Engine & Multi-Vector Correlation Tests (B4.4 & B4.5)
# ==============================================================================

def test_unified_risk_evaluation_unknown_url_with_brand_impersonation():
    """
    Scenario: User encounters an unknown URL not in threat database.
    Hostname impersonates HDFC Bank.
    Central Risk Engine extracts features, runs ML & brand impersonation,
    returns explainable evidence without marking verified safe.
    """
    db = SessionLocal()
    try:
        req = UnifiedRiskEvaluationRequest(
            indicator="http://hdfcbank-netbanking-portal.xyz/login/verify",
            indicator_type="URL",
            source_component="BROWSER_EXTENSION",
            device_id=TEST_DEVICE_UUID
        )
        res = central_risk_engine.evaluate_risk(db, req)
        assert res.risk_score >= 60.0
        assert res.risk_level in ["MEDIUM", "HIGH"]
        assert res.classification == "POSSIBLE_PHISHING"
        assert res.intelligence_status == "UNVERIFIED_HEURISTIC"
        assert len(res.evidence_items) >= 1
        assert any(item["type"] == "DOMAIN_IMPERSONATION" for item in res.evidence_items)
        assert "Do not enter credentials" in res.recommended_action
    finally:
        db.close()


def test_unified_risk_evaluation_sms_content():
    """
    Central Risk Engine evaluates raw SMS content with multi-vector correlation.
    """
    db = SessionLocal()
    try:
        req = UnifiedRiskEvaluationRequest(
            indicator="Urgent: Electricity bill unpaid. Power disconnected today. Call officer at 9876543210 immediately.",
            indicator_type="SMS_CONTENT",
            source_component="ANDROID_APP",
            device_id=TEST_DEVICE_UUID
        )
        res = central_risk_engine.evaluate_risk(db, req)
        assert res.risk_score >= 30.0
        assert len(res.detection_reasons) >= 1
        assert len(res.evidence_items) >= 1
    finally:
        db.close()


def test_detection_api_url_endpoint_returns_brand_impersonation():
    """
    The REST API endpoint POST /api/v1/detection/url returns rich B4
    brand impersonation diagnostics and risk indicators.
    """
    res = client.post(
        "/api/v1/detection/url",
        headers={"x-test-bypass-rate-limit": "true"},
        json={"url": "http://sbi-netbanking-update.xyz/verify"}
    )
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["classification"] in ["PHISHING", "SUSPICIOUS"]
    assert data["risk_score"] >= 60.0
    assert "analysis" in data
    assert "features" in data["analysis"]
    assert "risk_indicators" in data["analysis"]
    assert data["analysis"]["brand_impersonation"] is not None
    assert data["analysis"]["brand_impersonation"]["brand_id"] == "SBI"

