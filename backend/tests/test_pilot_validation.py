"""
backend/tests/test_pilot_validation.py
Stage 9: Pilot Validation, Monitoring, Feedback & Admin Operations Test Suite.
Validates end-to-end integration of Stage 9 observability, models, feeds, feedback,
feature flags, async jobs, and administrative access controls.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings
from app.core.feature_flags import feature_flags
from app.core.alert_manager import alert_manager

client = TestClient(app)

ADMIN_HEADERS = {"X-Admin-Key": settings.ADMIN_SECRET_KEY}
TEST_BYPASS = {"x-test-bypass-rate-limit": "true"}
COMBINED_ADMIN_HEADERS = {**ADMIN_HEADERS, **TEST_BYPASS}


# ---------------------------------------------------------------------------
# 1. Observability & Health Monitoring Tests
# ---------------------------------------------------------------------------

def test_detailed_health_endpoint():
    """Verify detailed subsystem health returns status for all components."""
    response = client.get("/api/v1/monitoring/health/detailed", headers=TEST_BYPASS)
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] in ["HEALTHY", "DEGRADED"]
    assert "services" in data
    services = data["services"]
    assert "api_server" in services
    assert "database" in services
    assert "ai_models" in services
    assert "threat_intelligence" in services
    assert "job_worker_pool" in services


def test_metrics_endpoint():
    """Verify performance metrics collection and summary statistics."""
    # Send a request first to ensure metrics are tracked
    client.get("/api/health", headers=TEST_BYPASS)

    response = client.get("/api/v1/monitoring/metrics", headers=TEST_BYPASS)
    assert response.status_code == 200
    data = response.json()
    assert "uptime_seconds" in data
    assert "total_requests" in data
    assert data["total_requests"] >= 1
    assert "latency_ms" in data
    assert "avg" in data["latency_ms"]
    assert "p95" in data["latency_ms"]
    assert "resource_usage" in data
    assert data["resource_usage"]["database_engine"] == "SQLite Relational"


def test_response_time_header():
    """Verify RequestObservabilityMiddleware attaches X-Response-Time-Ms header."""
    response = client.get("/api/health", headers=TEST_BYPASS)
    assert response.status_code == 200
    assert "X-Response-Time-Ms" in response.headers
    latency = float(response.headers["X-Response-Time-Ms"])
    assert latency >= 0.0


# ---------------------------------------------------------------------------
# 2. AI Model Monitoring & Drift Reports
# ---------------------------------------------------------------------------

def test_models_overview_endpoint():
    """Verify registry of all deployed AI models with benchmark evaluation metrics."""
    response = client.get("/api/v1/monitoring/models", headers=TEST_BYPASS)
    assert response.status_code == 200
    data = response.json()
    assert data["total_deployed_models"] == 3
    model_ids = [m["model_id"] for m in data["models"]]
    assert "PHISHING_URL_CLASSIFIER" in model_ids
    assert "COMMUNICATION_NLP_DETECTOR" in model_ids
    assert "VOICE_DEEPFAKE_DETECTOR" in model_ids

    # Check benchmark metrics are present and genuine
    phish = next(m for m in data["models"] if m["model_id"] == "PHISHING_URL_CLASSIFIER")
    assert phish["metrics"]["accuracy"] > 0.90
    assert "RandomForest" in phish["algorithm"]


def test_model_drift_report_phishing():
    """Verify input distribution drift reporting for phishing URL classifier."""
    response = client.get(
        "/api/v1/monitoring/models/PHISHING_URL_CLASSIFIER/drift",
        headers=TEST_BYPASS
    )
    assert response.status_code == 200
    data = response.json()
    assert data["model_id"] == "PHISHING_URL_CLASSIFIER"
    assert "baseline_distribution" in data
    assert "observed_distribution" in data
    assert "governance_rule" in data
    assert "Automatic production model retraining is strictly prohibited" in data["governance_rule"]


def test_model_drift_invalid_model():
    """Verify 404 for unknown model drift request."""
    response = client.get(
        "/api/v1/monitoring/models/NONEXISTENT_MODEL/drift",
        headers=TEST_BYPASS
    )
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# 3. Threat Intelligence Operations & Freshness
# ---------------------------------------------------------------------------

def test_feed_health_report():
    """Verify feed telemetry, freshness rating, and known limitations."""
    response = client.get("/api/v1/monitoring/feeds", headers=TEST_BYPASS)
    assert response.status_code == 200
    data = response.json()
    assert "summary" in data
    assert data["summary"]["total_sources_configured"] == 3
    assert len(data["sources"]) == 3

    sources_map = {s["key"]: s for s in data["sources"]}
    assert "URLHAUS" in sources_map
    assert "PHISHTANK" in sources_map
    assert "INTERNAL_VERIFIED" in sources_map
    assert "freshness" in sources_map["URLHAUS"]
    assert len(sources_map["URLHAUS"]["limitations"]) > 0


# ---------------------------------------------------------------------------
# 4. User Feedback Submission & Human Review
# ---------------------------------------------------------------------------

def test_submit_valid_feedback():
    """Verify submitting analysis feedback records to DB with review_status=PENDING."""
    payload = {
        "analysis_id": 1,
        "target_identifier": "https://test-example-phish.biz",
        "feedback_category": "FALSE_POSITIVE",
        "user_explanation": "This is our internal company development domain.",
        "user_provided_label": "LEGITIMATE"
    }
    response = client.post("/api/v1/feedback/submit", json=payload, headers=TEST_BYPASS)
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "RECEIVED"
    assert data["review_status"] == "PENDING"
    assert data["feedback_category"] == "FALSE_POSITIVE"
    assert "does not automatically modify AI models" in data["message"]


def test_submit_invalid_feedback_category():
    """Verify validation error on unknown feedback category."""
    payload = {
        "feedback_category": "COMPLETELY_MADE_UP_CATEGORY",
        "user_explanation": "testing invalid category"
    }
    response = client.post("/api/v1/feedback/submit", json=payload, headers=TEST_BYPASS)
    assert response.status_code == 422


def test_feedback_history():
    """Verify querying recent feedback submissions."""
    response = client.get("/api/v1/feedback/history?limit=10", headers=TEST_BYPASS)
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert isinstance(data["feedback"], list)


# ---------------------------------------------------------------------------
# 5. Admin Authentication & Operations Center
# ---------------------------------------------------------------------------

def test_admin_endpoints_require_auth():
    """Verify admin endpoints reject requests without valid X-Admin-Key."""
    # No header
    res1 = client.get("/api/v1/admin/overview", headers=TEST_BYPASS)
    assert res1.status_code == 401

    # Wrong key
    res2 = client.get(
        "/api/v1/admin/overview",
        headers={"X-Admin-Key": "wrong-secret-key", **TEST_BYPASS}
    )
    assert res2.status_code == 401


def test_admin_overview_authorized():
    """Verify admin overview delivers aggregated platform telemetry when authenticated."""
    response = client.get("/api/v1/admin/overview", headers=COMBINED_ADMIN_HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert data["platform"] == settings.APP_NAME
    assert "overall_health" in data
    assert "performance" in data
    assert "ai_models" in data
    assert "feature_flags" in data


def test_admin_feature_flags_management():
    """Verify listing and updating feature flags through admin API."""
    # List flags
    res_list = client.get("/api/v1/admin/feature-flags", headers=COMBINED_ADMIN_HEADERS)
    assert res_list.status_code == 200
    flags = res_list.json()["feature_flags"]
    assert "enable_audio_analysis" in flags
    assert "maintenance_mode" in flags

    # Toggle a flag
    res_patch = client.patch(
        "/api/v1/admin/feature-flags/enable_audio_analysis",
        json={"enabled": False},
        headers=COMBINED_ADMIN_HEADERS
    )
    assert res_patch.status_code == 200
    assert res_patch.json()["enabled"] is False
    assert not feature_flags.is_enabled("enable_audio_analysis")

    # Restore flag
    res_restore = client.patch(
        "/api/v1/admin/feature-flags/enable_audio_analysis",
        json={"enabled": True},
        headers=COMBINED_ADMIN_HEADERS
    )
    assert res_restore.status_code == 200
    assert feature_flags.is_enabled("enable_audio_analysis")


def test_admin_feedback_review_workflow():
    """Verify human reviewer can inspect pending feedback and record a verdict."""
    # 1. Submit feedback
    client.post(
        "/api/v1/feedback/submit",
        json={
            "target_identifier": "https://suspicious-review-test.net",
            "feedback_category": "FALSE_NEGATIVE",
            "user_explanation": "Missed malicious login page."
        },
        headers=TEST_BYPASS
    )

    # 2. Get pending items
    res_pending = client.get("/api/v1/admin/feedback/pending", headers=COMBINED_ADMIN_HEADERS)
    assert res_pending.status_code == 200
    pending_items = res_pending.json()["feedback"]
    assert len(pending_items) > 0
    feedback_id = pending_items[0]["feedback_id"]

    # 3. Submit review verdict
    res_review = client.patch(
        f"/api/v1/admin/feedback/{feedback_id}/review",
        json={
            "review_status": "CONFIRMED",
            "reviewer_notes": "Verified by SOC analyst. Added to candidate retraining pool.",
            "reviewed_by": "lead_soc_analyst"
        },
        headers=COMBINED_ADMIN_HEADERS
    )
    assert res_review.status_code == 200
    data = res_review.json()
    assert data["new_review_status"] == "CONFIRMED"
    assert data["reviewed_by"] == "lead_soc_analyst"


def test_admin_alerts_workflow():
    """Verify alert creation, listing, and acknowledgement workflow."""
    # Create an alert
    alert_manager.create_alert(
        alert_type="BACKEND_DEGRADED",
        source="TEST_SUITE",
        message="Simulated test warning alert",
        severity="WARNING"
    )

    # List alerts
    res_alerts = client.get("/api/v1/admin/alerts", headers=COMBINED_ADMIN_HEADERS)
    assert res_alerts.status_code == 200
    alerts_data = res_alerts.json()
    assert alerts_data["summary"]["active_alerts"] >= 1

    # Clear/acknowledge all
    res_clear = client.post("/api/v1/admin/alerts/clear", headers=COMBINED_ADMIN_HEADERS)
    assert res_clear.status_code == 200
    assert res_clear.json()["acknowledged_count"] >= 1


def test_admin_model_candidate_governance():
    """Verify model pipeline requires manual review and enforces governance rules."""
    response = client.get("/api/v1/admin/model-candidates", headers=COMBINED_ADMIN_HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert data["pipeline_status"] == "MANUAL_REVIEW_REQUIRED"
    assert "Automatic retraining from user feedback or input drift is strictly prohibited" in data["governance_statement"]


# ---------------------------------------------------------------------------
# 6. Asynchronous Jobs & SSE Streaming
# ---------------------------------------------------------------------------

def test_async_job_submission_and_status():
    """Verify asynchronous job creation, queueing, and status retrieval."""
    payload = {
        "job_type": "URL_ANALYSIS",
        "url": "https://example.com/login"
    }
    response = client.post("/api/v1/jobs/submit", json=payload, headers=TEST_BYPASS)
    assert response.status_code == 202
    data = response.json()
    assert "job_id" in data
    job_id = data["job_id"]
    assert data["status"] in ["QUEUED", "PROCESSING", "COMPLETED"]

    # Poll status
    status_res = client.get(f"/api/v1/jobs/{job_id}", headers=TEST_BYPASS)
    assert status_res.status_code == 200
    assert status_res.json()["job_id"] == job_id


def test_list_recent_jobs():
    """Verify listing recent asynchronous analysis jobs."""
    response = client.get("/api/v1/jobs?limit=5", headers=TEST_BYPASS)
    assert response.status_code == 200
    data = response.json()
    assert "jobs" in data
    assert "total_active_jobs" in data
    assert isinstance(data["jobs"], list)


# ---------------------------------------------------------------------------
# 7. Maintenance Mode Guard Behavior
# ---------------------------------------------------------------------------

def test_maintenance_mode_guard():
    """Verify maintenance mode blocks public analysis endpoints with 503."""
    # Enable maintenance mode
    feature_flags.set_flag("maintenance_mode", True)

    try:
        # Public analysis should return 503
        res = client.post(
            "/api/v1/detection/url",
            json={"url": "https://test.com"},
            headers=TEST_BYPASS
        )
        assert res.status_code == 503
        assert "Maintenance Mode" in res.json()["error"]

        # Health checks must still pass
        res_health = client.get("/api/health", headers=TEST_BYPASS)
        assert res_health.status_code == 200

        # Admin overview must still pass
        res_admin = client.get("/api/v1/admin/overview", headers=COMBINED_ADMIN_HEADERS)
        assert res_admin.status_code == 200
    finally:
        # Always restore maintenance mode to False
        feature_flags.set_flag("maintenance_mode", False)
