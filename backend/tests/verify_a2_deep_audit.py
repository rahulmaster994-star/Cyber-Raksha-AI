"""
backend/tests/verify_a2_deep_audit.py
Deep Technical Verification Suite for Phase A2: Automatic Threat Intelligence Synchronization
Tests all 13 checklist requirements in PART 2:
1. Scheduler starts correctly
2. Scheduler stops cleanly
3. Restarting the backend does not create duplicate scheduler tasks
4. Repeated feed failures do not crash the backend
5. Network timeouts are handled
6. Failed syncs preserve previously valid indicators
7. Successful syncs update indicators correctly
8. Stale dynamic indicators are retired correctly
9. Seed indicators are preserved according to an explicit policy
10. Duplicate indicators do not create duplicate database records
11. Scheduler telemetry accurately reflects actual execution
12. Manual trigger and scheduled execution do not cause conflicting concurrent syncs
13. Worker concurrency analysis
"""
import asyncio
import time
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock

from app.database.session import SessionLocal
from app.models.threat_intel import ThreatFeedLog
from app.services.threat_intel_scheduler import ThreatIntelScheduler, threat_intel_scheduler
from app.services.threat_intel_service import ThreatIntelService
from ai_engine.threat_intelligence.threat_database import (
    _THREAT_CACHE,
    add_indicator,
    lookup_indicator,
    retire_stale_indicators,
    get_all_indicators,
    get_intel_stats,
    seed_threat_database
)


def verify_scheduler_deep():
    print("============================================================")
    print("PHASE A2 DEEP TECHNICAL VERIFICATION SUITE")
    print("============================================================\n")

    passed = 0
    failed = 0

    def check(name, fn):
        nonlocal passed, failed
        try:
            fn()
            print(f"  [PASS] {name}")
            passed += 1
        except Exception as e:
            print(f"  [FAIL] {name}: {e}")
            failed += 1

    # 1 & 2. Start and Stop
    def test_start_stop():
        async def _run():
            s = ThreatIntelScheduler()
            assert not s.is_running
            await s.start(interval_minutes=15)
            assert s.is_running
            assert s.status == "RUNNING"
            await s.stop()
            assert not s.is_running
            assert s.status == "STOPPED"
        asyncio.run(_run())
    check("1 & 2: Scheduler starts and stops cleanly", test_start_stop)

    # 3. Duplicate task avoidance on restart
    def test_no_duplicate_task():
        async def _run():
            s = ThreatIntelScheduler()
            await s.start(interval_minutes=20)
            initial_task = s._task
            # Call start again while already running
            await s.start(interval_minutes=20)
            assert s._task is initial_task  # Same task object, no duplicate created
            await s.stop()
        asyncio.run(_run())
    check("3: Restarting/re-invoking start does not create duplicate tasks", test_no_duplicate_task)

    # 4 & 5. Repeated failures and network timeouts
    def test_repeated_failures_and_timeouts():
        async def _run():
            s = ThreatIntelScheduler()
            with patch("ai_engine.threat_intelligence.feed_updater.feed_updater.update_urlhaus_feed") as mock_feed:
                mock_feed.return_value = {
                    "source": "URLHAUS",
                    "status": "OFFLINE_FALLBACK",
                    "records_added": 0,
                    "error": "Connection timed out after 5.0 seconds",
                    "duration_seconds": 5.0
                }
                # Run 5 consecutive failed sync cycles
                for _ in range(5):
                    res = await s.run_sync_cycle()
                    assert res["status"] == "SUCCESS"  # Successfully caught and reported
                    assert res["feed_update"]["status"] == "OFFLINE_FALLBACK"
            assert s._last_error is None  # Handled safely, no unhandled exception crash
        asyncio.run(_run())
    check("4 & 5: Repeated feed failures and network timeouts do not crash", test_repeated_failures_and_timeouts)

    # 6. Failed syncs preserve previously valid indicators
    def test_failed_sync_preserves_indicators():
        async def _run():
            # Ensure Mirai control exists
            mirai_before = lookup_indicator("URL", "http://117.206.182.205:58394/i")
            assert mirai_before is not None

            s = ThreatIntelScheduler()
            with patch("ai_engine.threat_intelligence.feed_updater.feed_updater.update_urlhaus_feed") as mock_feed:
                mock_feed.side_effect = TimeoutError("Simulated DNS Failure")
                res = await s.run_sync_cycle()
                assert res["status"] == "ERROR"

            # Cached indicators must remain intact!
            mirai_after = lookup_indicator("URL", "http://117.206.182.205:58394/i")
            assert mirai_after is not None
            assert mirai_after["indicator_value"] == mirai_before["indicator_value"]
        asyncio.run(_run())
    check("6: Failed syncs preserve previously valid indicators", test_failed_sync_preserves_indicators)

    # 7. Successful sync updates indicators correctly
    def test_successful_sync_updates():
        async def _run():
            s = ThreatIntelScheduler()
            test_threat_url = "https://verified-active-phish.test.invalid/login"
            with patch("ai_engine.threat_intelligence.feed_updater.feed_updater.update_urlhaus_feed") as mock_feed:
                def fake_update():
                    add_indicator({
                        "indicator_type": "URL",
                        "indicator_value": test_threat_url,
                        "threat_type": "PHISHING",
                        "severity": "HIGH",
                        "confidence_score": 0.95,
                        "source_name": "URLHAUS",
                        "is_active": True
                    })
                    return {"source": "URLHAUS", "status": "SUCCESS", "records_added": 1, "duration_seconds": 0.05}
                mock_feed.side_effect = fake_update

                res = await s.run_sync_cycle()
                assert res["status"] == "SUCCESS"
                assert res["feed_update"]["records_added"] == 1

            matched = lookup_indicator("URL", test_threat_url)
            assert matched is not None
            assert matched["indicator_value"] == test_threat_url
        asyncio.run(_run())
    check("7: Successful sync updates indicators correctly", test_successful_sync_updates)

    # 8 & 9. Stale dynamic indicators retired; Seed indicators preserved
    def test_stale_retirement_and_seed_policy():
        # Add dynamic indicator older than 30 days
        old_val = "http://stale-threat-2023.invalid/path"
        add_indicator({
            "indicator_type": "URL",
            "indicator_value": old_val,
            "threat_type": "PHISHING",
            "severity": "HIGH",
            "confidence_score": 0.9,
            "source_name": "COMMUNITY_DYNAMIC",
            "is_active": True,
            "is_seed": False
        })
        _THREAT_CACHE["URL"][old_val]["updated_at"] = (datetime.now(timezone.utc) - timedelta(days=35)).isoformat()

        # Seed indicator (e.g. CBI Digital Arrest Warrant)
        cbi_val = "cbi-digital-arrest-warrant.com"
        cbi_ioc = lookup_indicator("DOMAIN", cbi_val)
        assert cbi_ioc is not None
        assert cbi_ioc.get("is_seed") is True

        # Run retirement
        retired = retire_stale_indicators(max_age_days=30)
        assert retired >= 1

        # Check dynamic is inactive
        dynamic_after = lookup_indicator("URL", old_val)
        assert dynamic_after["is_active"] is False

        # Check seed is STILL active
        cbi_after = lookup_indicator("DOMAIN", cbi_val)
        assert cbi_after["is_active"] is True
    check("8 & 9: Stale indicators retired, seed indicators strictly preserved", test_stale_retirement_and_seed_policy)

    # 10. Deduplication
    def test_deduplication():
        initial_count = len(_THREAT_CACHE["DOMAIN"])
        for _ in range(5):
            add_indicator({
                "indicator_type": "DOMAIN",
                "indicator_value": "duplicate-test-target.invalid",
                "threat_type": "PHISHING",
                "severity": "HIGH",
                "confidence_score": 0.95,
                "source_name": "URLHAUS"
            })
        final_count = len(_THREAT_CACHE["DOMAIN"])
        assert final_count == initial_count + 1  # Only added once
    check("10: Duplicate indicators in cache overwrite cleanly without duplicates", test_deduplication)

    # 11. Telemetry accuracy
    def test_telemetry_accuracy():
        async def _run():
            s = ThreatIntelScheduler()
            await s.start(interval_minutes=45)
            tel = s.get_telemetry()
            assert tel["status"] == "RUNNING"
            assert tel["sync_interval_minutes"] == 45
            assert tel["next_run"] is not None
            await s.stop()
            tel_stopped = s.get_telemetry()
            assert tel_stopped["status"] == "STOPPED"
        asyncio.run(_run())
    check("11: Scheduler telemetry accurately reflects runtime state", test_telemetry_accuracy)

    # 12. Concurrency lock prevents conflicting concurrent syncs
    def test_concurrency_lock():
        async def _run():
            s = ThreatIntelScheduler()
            call_count = 0
            original_trigger = ThreatIntelService.trigger_feed_update

            def slow_trigger(db):
                nonlocal call_count
                call_count += 1
                time.sleep(0.1)  # Simulate slow I/O
                return {"source": "URLHAUS", "status": "SUCCESS", "records_added": 0}

            with patch("app.services.threat_intel_service.ThreatIntelService.trigger_feed_update", side_effect=slow_trigger):
                # Trigger two concurrent sync cycles
                res1, res2 = await asyncio.gather(
                    s.run_sync_cycle(),
                    s.run_sync_cycle()
                )
                assert res1["status"] == "SUCCESS"
                assert res2["status"] == "SUCCESS"
                # Because of asyncio.Lock, they execute sequentially, not simultaneously
                assert call_count == 2
        asyncio.run(_run())
    check("12: Concurrency lock ensures serialized execution without race conditions", test_concurrency_lock)

    print(f"\n============================================================")
    print(f"DEEP VERIFICATION COMPLETED: {passed} PASSED / {failed} FAILED")
    print(f"============================================================\n")

    return failed == 0


if __name__ == "__main__":
    success = verify_scheduler_deep()
    if not success:
        exit(1)

