"""
backend/app/core/observability.py
Stage 9: System Observability, Structured Performance Metrics & Detailed Health Checker.
Monitors API latency percentiles, error rates, model readiness, and memory footprint.
"""
import time
import os
import sys
from typing import Dict, Any, List
from datetime import datetime, timezone
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.database.session import check_db_connection
from app.services.threat_intel_ops import threat_intel_ops
from ai_engine.core.model_manager import model_manager
from ai_engine.inference.communication_detector import communication_detector
from ai_engine.inference.audio_detector import audio_detector


class MetricsTracker:
    """
    In-memory performance and latency tracker.
    Stores rolling latencies to compute min, avg, p50, p95, p99, and error counts.
    """
    def __init__(self, max_samples: int = 1000):
        self._max_samples = max_samples
        self._latencies: List[float] = []
        self._total_requests: int = 0
        self._total_errors: int = 0
        self._endpoint_latencies: Dict[str, List[float]] = {}
        self._status_counts: Dict[int, int] = {}
        self._start_time = time.time()

    def record_request(self, endpoint: str, status_code: int, latency_ms: float):
        self._total_requests += 1
        self._status_counts[status_code] = self._status_counts.get(status_code, 0) + 1
        if status_code >= 400:
            self._total_errors += 1

        if len(self._latencies) >= self._max_samples:
            self._latencies.pop(0)
        self._latencies.append(latency_ms)

        # Record per endpoint
        clean_ep = endpoint.split("?")[0]
        if clean_ep not in self._endpoint_latencies:
            self._endpoint_latencies[clean_ep] = []
        ep_list = self._endpoint_latencies[clean_ep]
        if len(ep_list) >= 100:
            ep_list.pop(0)
        ep_list.append(latency_ms)

    def get_metrics_summary(self) -> Dict[str, Any]:
        lats = sorted(self._latencies)
        count = len(lats)

        if count > 0:
            avg_lat = round(sum(lats) / count, 2)
            min_lat = round(lats[0], 2)
            max_lat = round(lats[-1], 2)
            p50 = round(lats[int(count * 0.50)], 2)
            p95 = round(lats[min(int(count * 0.95), count - 1)], 2)
            p99 = round(lats[min(int(count * 0.99), count - 1)], 2)
        else:
            avg_lat = min_lat = max_lat = p50 = p95 = p99 = 0.0

        error_rate_pct = round((self._total_errors / self._total_requests * 100), 2) if self._total_requests > 0 else 0.0

        endpoint_breakdown = {}
        for ep, ep_lats in self._endpoint_latencies.items():
            if ep_lats:
                endpoint_breakdown[ep] = {
                    "count": len(ep_lats),
                    "avg_ms": round(sum(ep_lats) / len(ep_lats), 2),
                    "p95_ms": round(sorted(ep_lats)[min(int(len(ep_lats) * 0.95), len(ep_lats) - 1)], 2)
                }

        # Resource monitoring (zero-budget compatible)
        db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "cyber_raksha.db"))
        db_size_kb = round(os.path.getsize(db_path) / 1024, 1) if os.path.exists(db_path) else 0.0

        return {
            "uptime_seconds": round(time.time() - self._start_time, 1),
            "total_requests": self._total_requests,
            "total_errors": self._total_errors,
            "error_rate_percent": error_rate_pct,
            "latency_ms": {
                "samples_tracked": count,
                "avg": avg_lat,
                "min": min_lat,
                "p50_median": p50,
                "p95": p95,
                "p99": p99,
                "max": max_lat
            },
            "status_codes": self._status_counts,
            "top_endpoints": endpoint_breakdown,
            "resource_usage": {
                "database_size_kb": db_size_kb,
                "database_engine": "SQLite Relational",
                "python_version": sys.version.split()[0]
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


metrics_tracker = MetricsTracker()


class RequestObservabilityMiddleware(BaseHTTPMiddleware):
    """
    Measures duration of every request and logs operational latency.
    Excludes sensitive query params or body logging to protect privacy.
    """
    async def dispatch(self, request: Request, call_next) -> Response:
        start = time.time()
        response = await call_next(request)
        duration_ms = (time.time() - start) * 1000.0

        metrics_tracker.record_request(
            endpoint=request.url.path,
            status_code=response.status_code,
            latency_ms=duration_ms
        )

        response.headers["X-Response-Time-Ms"] = f"{duration_ms:.2f}"
        return response


def get_detailed_health_status() -> Dict[str, Any]:
    """
    Evaluates individual health states of backend subsystems.
    Distinguishes application running vs degraded subcomponents.
    """
    # 1. Database
    is_db_connected, db_latency_ms, db_msg = check_db_connection()
    db_status = "HEALTHY" if is_db_connected else "UNAVAILABLE"

    # 2. AI Models
    model_manager.load_model()
    phish_status = model_manager.get_status()
    phish_ready = phish_status.get("model_loaded", False)
    comm_status = communication_detector.get_status()
    audio_status = audio_detector.get_status()

    models_health = {
        "phishing_url_model": "READY" if phish_ready else "DEGRADED",
        "communication_nlp_model": "READY" if comm_status.get("model_loaded") else "DEGRADED",
        "voice_deepfake_detector": "READY" if audio_status.get("model_loaded") else "DEGRADED"
    }

    all_models_ready = all(v == "READY" for v in models_health.values())

    # 3. Threat Intel
    feed_report = threat_intel_ops.get_feed_health_report()
    threat_intel_healthy = feed_report["summary"]["healthy_sources"] > 0

    # Overall Platform Health
    if is_db_connected and all_models_ready and threat_intel_healthy:
        overall_status = "HEALTHY"
    elif is_db_connected:
        overall_status = "DEGRADED"
    else:
        overall_status = "CRITICAL_OUTAGE"

    return {
        "status": overall_status,
        "services": {
            "api_server": "HEALTHY",
            "database": {
                "status": db_status,
                "latency_ms": db_latency_ms,
                "detail": db_msg
            },
            "ai_models": {
                "status": "HEALTHY" if all_models_ready else "DEGRADED",
                "subsystems": models_health
            },
            "threat_intelligence": {
                "status": "HEALTHY" if threat_intel_healthy else "STALE",
                "healthy_sources": feed_report["summary"]["healthy_sources"],
                "active_indicators": feed_report["summary"]["total_active_indicators_in_db"]
            },
            "job_worker_pool": {
                "status": "ACTIVE",
                "max_workers": 4
            }
        },
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

