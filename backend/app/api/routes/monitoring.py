"""
backend/app/api/routes/monitoring.py
Stage 9: System Observability & Health Monitoring Endpoints.
Provides detailed health checks, performance metrics, model monitoring, and feed health.
"""
from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from app.core.observability import metrics_tracker, get_detailed_health_status
from app.services.model_monitor import model_monitor
from app.services.threat_intel_ops import threat_intel_ops

router = APIRouter(tags=["Monitoring & Observability"])


@router.get(
    "/monitoring/health/detailed",
    status_code=status.HTTP_200_OK,
    summary="Detailed System Health Status",
    description=(
        "Returns the health status of every backend subsystem: database, AI models, "
        "threat intelligence feeds, and the job worker pool."
    ),
)
def get_detailed_health():
    """Full subsystem health check with per-service status breakdown."""
    return get_detailed_health_status()


@router.get(
    "/monitoring/metrics",
    status_code=status.HTTP_200_OK,
    summary="API Performance Metrics",
    description=(
        "Returns rolling latency statistics (avg, p50, p95, p99), error rate, "
        "per-endpoint breakdowns, and resource usage."
    ),
)
def get_performance_metrics():
    """Return real-time performance metrics collected since server startup."""
    return metrics_tracker.get_metrics_summary()


@router.get(
    "/monitoring/models",
    status_code=status.HTTP_200_OK,
    summary="AI Model Registry Overview",
    description="Lists all deployed AI models with their version, algorithm, evaluation metrics and deployment status.",
)
def get_models_overview():
    """Return the full model registry with benchmark metrics."""
    return model_monitor.get_models_overview()


@router.get(
    "/monitoring/models/{model_id}/drift",
    status_code=status.HTTP_200_OK,
    summary="AI Model Input Distribution Drift Report",
    description=(
        "Returns a comparison of baseline training distribution vs live observed "
        "input statistics for the specified model, with drift signals and governance rules."
    ),
)
def get_model_drift_report(model_id: str):
    """
    Return drift monitoring report for a specific model.

    Valid model_id values:
    - PHISHING_URL_CLASSIFIER
    - COMMUNICATION_NLP_DETECTOR
    - VOICE_DEEPFAKE_DETECTOR
    """
    model_id_upper = model_id.upper()
    report = model_monitor.get_model_drift_report(model_id_upper)
    if "error" in report:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "error": "Model Not Found",
                "detail": report["error"],
                "valid_model_ids": [
                    "PHISHING_URL_CLASSIFIER",
                    "COMMUNICATION_NLP_DETECTOR",
                    "VOICE_DEEPFAKE_DETECTOR",
                ],
            },
        )
    return report


@router.get(
    "/monitoring/feeds",
    status_code=status.HTTP_200_OK,
    summary="Threat Intelligence Feed Health",
    description=(
        "Returns the operational health, freshness, import statistics, "
        "and known limitations of all configured threat intelligence sources."
    ),
)
def get_feed_health():
    """Return comprehensive threat intelligence feed health report."""
    return threat_intel_ops.get_feed_health_report()

