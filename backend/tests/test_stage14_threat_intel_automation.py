"""
backend/tests/test_stage14_threat_intel_automation.py
Automated Verification Suite for Phase A2: Automatic Threat Intelligence Synchronization.
Verifies scheduler lifecycle, periodic execution, stale indicator retirement,
offline resilience, and telemetry endpoints.
"""
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch
from fastapi.testclient import TestClient

from app.main import app
from app.core.config import settings
from app.database.session import SessionLocal
from app.models.threat_intel import ThreatFeedLog
from app.services.threat_intel_scheduler import ThreatIntelScheduler, threat_intel_scheduler
from ai_engine.threat_intelligence.threat_database import (
    add_indicator,
    lookup_indicator,
    retire_stale_indicators,
    get_all_indicators,
    get_intel_stats
)

client = TestClient(app)


def test_scheduler_status_endpoints():
    """Verify that both /status and /scheduler/status surface real-time telemetry."""
    # 1. Check /api/v1/intel/status
    res = client.get("/api/v1/intel/status")
    assert res.status_code == 200
    data = res.json()
    assert "auto_sync_enabled" in data
    assert "sync_interval_minutes" in data
    assert "scheduler_status" in data
    assert data["auto_sync_enabled"] is True
    assert data["sync_interval_minutes"] == settings.THREAT_INTEL_SYNC_INTERVAL_MINUTES

    # 2. Check /api/v1/intel/scheduler/status
    res_sched = client.get("/api/v1/intel/scheduler/status")
    assert res_sched.status_code == 200
    sched_data = res_sched.json()
    assert "enabled" in sched_data
    assert "status" in sched_data
    assert "sync_interval_minutes" in sched_data
    assert "runs_completed" in sched_data


def test_scheduler_lifecycle():
    """Verify that ThreatIntelScheduler starts and stops cleanly without task leaks."""
    import asyncio
    async def _test():
        scheduler = ThreatIntelScheduler()
        assert scheduler.is_running is False

        # Start with 30 minute interval
        await scheduler.start(interval_minutes=30)
        assert scheduler.is_running is True
        assert scheduler.status == "RUNNING"
        telemetry = scheduler.get_telemetry()
        assert telemetry["sync_interval_minutes"] == 30
        assert telemetry["next_run"] is not None

        # Calling start again while running should be a safe no-op
        await scheduler.start(interval_minutes=30)
        assert scheduler.is_running is True

        # Stop scheduler
        await scheduler.stop()
        assert scheduler.is_running is False
        assert scheduler.status == "STOPPED"

    asyncio.run(_test())


def test_scheduler_sync_cycle_execution():
    """Verify manual execution of run_sync_cycle and persistence in ThreatFeedLog."""
    import asyncio
    async def _test():
        scheduler = ThreatIntelScheduler()
        initial_runs = scheduler._runs_completed

        cycle_res = await scheduler.run_sync_cycle()
        assert cycle_res["status"] in ["SUCCESS", "OFFLINE_FALLBACK"]
        assert "feed_update" in cycle_res
        assert "retired_stale_indicators" in cycle_res
        assert scheduler._runs_completed == initial_runs + 1
        assert scheduler._last_run is not None

        # Check ThreatFeedLog record was written to DB
        db = SessionLocal()
        try:
            latest_log = db.query(ThreatFeedLog).order_by(ThreatFeedLog.id.desc()).first()
            assert latest_log is not None
            assert latest_log.source_name == "URLHAUS"
            assert latest_log.status in ["SUCCESS", "OFFLINE_FALLBACK"]
        finally:
            db.close()

    asyncio.run(_test())


def test_scheduler_trigger_endpoint():
    """Verify POST /api/v1/intel/scheduler/trigger forces an immediate sync cycle."""
    res = client.post("/api/v1/intel/scheduler/trigger")
    assert res.status_code == 200
    data = res.json()
    assert "status" in data
    assert "feed_update" in data
    assert "retired_stale_indicators" in data


def test_stale_indicator_retirement_and_seed_preservation():
    """
    Verify that indicators older than TTL are deactivated,
    while seeded critical threat controls remain permanently active.
    """
    # 1. Add an old dynamic indicator (45 days old)
    old_time = (datetime.now(timezone.utc) - timedelta(days=45)).isoformat()
    dynamic_threat = {
        "indicator_type": "URL",
        "indicator_value": "http://temporary-phish-2024.xyz/login",
        "threat_type": "PHISHING",
        "severity": "HIGH",
        "confidence_score": 0.90,
        "source_name": "COMMUNITY_DYNAMIC",
        "is_active": True,
        "is_seed": False
    }
    add_indicator(dynamic_threat)

    # Force its updated_at to 45 days ago
    from ai_engine.threat_intelligence.threat_database import _THREAT_CACHE
    _THREAT_CACHE["URL"]["http://temporary-phish-2024.xyz/login"]["updated_at"] = old_time

    # 2. Add a recent dynamic indicator (2 days old)
    recent_time = (datetime.now(timezone.utc) - timedelta(days=2)).isoformat()
    recent_threat = {
        "indicator_type": "URL",
        "indicator_value": "http://active-credential-stealer.xyz/auth",
        "threat_type": "PHISHING",
        "severity": "HIGH",
        "confidence_score": 0.92,
        "source_name": "COMMUNITY_DYNAMIC",
        "is_active": True,
        "is_seed": False
    }
    add_indicator(recent_threat)
    _THREAT_CACHE["URL"]["http://active-credential-stealer.xyz/auth"]["updated_at"] = recent_time

    # 3. Execute retirement with 30-day cutoff
    retired_count = retire_stale_indicators(max_age_days=30)
    assert retired_count >= 1

    # Verify old indicator is retired (is_active = False)
    old_indicator = lookup_indicator("URL", "http://temporary-phish-2024.xyz/login")
    assert old_indicator is not None
    assert old_indicator["is_active"] is False

    # Verify recent indicator remains active
    rec_indicator = lookup_indicator("URL", "http://active-credential-stealer.xyz/auth")
    assert rec_indicator is not None
    assert rec_indicator["is_active"] is True

    # Verify seed indicators (e.g. Mirai botnet control) are NEVER retired
    mirai_indicator = lookup_indicator("URL", "http://117.206.182.205:58394/i")
    assert mirai_indicator is not None
    assert mirai_indicator["is_active"] is True
    assert mirai_indicator.get("is_seed") is True


def test_active_only_indicator_filtering():
    """Verify that /api/v1/intel/indicators filters active vs all indicators correctly."""
    res_active = client.get("/api/v1/intel/indicators?active_only=true")
    assert res_active.status_code == 200
    active_items = res_active.json()
    assert all(item["is_active"] is True for item in active_items)

    res_all = client.get("/api/v1/intel/indicators?active_only=false")
    assert res_all.status_code == 200
    all_items = res_all.json()
    # At least the retired indicator exists in all_items
    assert len(all_items) >= len(active_items)


def test_offline_fallback_resilience():
    """
    Verify that when external feed URLs are unreachable or time out,
    the scheduler handles the error safely without unhandled exceptions.
    """
    import asyncio
    async def _test():
        scheduler = ThreatIntelScheduler()

        # Simulate network timeout during feed fetch
        with patch("ai_engine.threat_intelligence.feed_updater.feed_updater.update_urlhaus_feed") as mock_feed:
            mock_feed.return_value = {
                "source": "URLHAUS",
                "status": "OFFLINE_FALLBACK",
                "records_added": 0,
                "error": "Simulated Network Timeout ConnectionRefusedError",
                "duration_seconds": 0.05
            }

            cycle_res = await scheduler.run_sync_cycle()
            assert cycle_res["status"] == "SUCCESS"  # Handled safely via OFFLINE_FALLBACK
            assert cycle_res["feed_update"]["status"] == "OFFLINE_FALLBACK"
            assert scheduler._last_error is None  # Handled gracefully, not an unhandled crash

    asyncio.run(_test())
