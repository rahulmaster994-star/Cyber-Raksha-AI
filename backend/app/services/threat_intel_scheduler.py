"""
backend/app/services/threat_intel_scheduler.py
Phase A2: Automatic Threat Intelligence Synchronization Scheduler.
Provides background scheduled threat feed ingestion, stale indicator pruning,
and telemetry reporting for Cyber Raksha AI.
"""
import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional

from app.core.config import settings
from app.database.session import SessionLocal

logger = logging.getLogger("cyber_raksha.threat_intel_scheduler")


class ThreatIntelScheduler:
    def __init__(self):
        self._task: Optional[asyncio.Task] = None
        self._running: bool = False
        self._interval_minutes: int = settings.THREAT_INTEL_SYNC_INTERVAL_MINUTES
        self._last_run: Optional[str] = None
        self._next_run: Optional[str] = None
        self._runs_completed: int = 0
        self._last_error: Optional[str] = None
        self._last_result: Optional[Dict[str, Any]] = None
        self._status: str = "INITIALIZED"
        self._lock = asyncio.Lock()

    @property
    def is_running(self) -> bool:
        return self._running and self._task is not None and not self._task.done()

    @property
    def status(self) -> str:
        if self.is_running:
            return "RUNNING"
        return self._status if self._status != "INITIALIZED" else "STOPPED"

    def get_telemetry(self) -> Dict[str, Any]:
        """Returns scheduler operational status and execution timestamps."""
        return {
            "enabled": settings.THREAT_INTEL_AUTO_SYNC_ENABLED,
            "status": self.status,
            "sync_interval_minutes": self._interval_minutes,
            "last_run": self._last_run,
            "next_run": self._next_run,
            "runs_completed": self._runs_completed,
            "last_error": self._last_error,
            "last_result": self._last_result
        }

    async def start(self, interval_minutes: Optional[int] = None):
        """Starts the background synchronization loop."""
        if not settings.THREAT_INTEL_AUTO_SYNC_ENABLED:
            self._status = "DISABLED_BY_CONFIG"
            logger.info("Threat intel automatic synchronization is disabled by configuration.")
            return

        if self.is_running:
            logger.warning("Threat intel scheduler is already running.")
            return

        if interval_minutes and interval_minutes > 0:
            self._interval_minutes = interval_minutes

        self._running = True
        self._status = "RUNNING"
        self._calculate_next_run()
        self._task = asyncio.create_task(self._scheduler_loop(), name="threat_intel_scheduler_task")
        logger.info(
            f"Threat intel scheduler started. Interval: {self._interval_minutes}m. "
            f"Next run: {self._next_run}"
        )

    async def stop(self):
        """Gracefully halts the background scheduler."""
        if not self._running and not self._task:
            self._status = "STOPPED"
            return

        self._running = False
        self._status = "STOPPED"
        self._next_run = None

        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            except Exception as e:
                logger.error(f"Error while stopping threat intel scheduler: {e}")
        self._task = None
        logger.info("Threat intel scheduler stopped.")

    def _calculate_next_run(self):
        now = datetime.now(timezone.utc)
        next_dt = now + timedelta(minutes=self._interval_minutes)
        self._next_run = next_dt.isoformat()

    async def run_sync_cycle(self) -> Dict[str, Any]:
        """
        Executes one full synchronization cycle:
        1. Ingests feed indicators from URLhaus/external sources.
        2. Retires stale indicators older than TTL.
        3. Updates logs and telemetry.
        Protected by asyncio.Lock to prevent concurrent duplicate runs.
        """
        async with self._lock:
            start_time = datetime.now(timezone.utc)
            self._last_run = start_time.isoformat()
            
            # Avoid circular imports
            from app.services.threat_intel_service import ThreatIntelService
            from ai_engine.threat_intelligence.threat_database import retire_stale_indicators
            from app.services.notification_service import notification_service
            from app.schemas.notification import NotificationCreate

            db = SessionLocal()
            try:
                # 1. Feed update
                feed_res = ThreatIntelService.trigger_feed_update(db)

                # 2. Stale indicators retirement
                retired_count = retire_stale_indicators(max_age_days=settings.THREAT_INDICATOR_TTL_DAYS)

                cycle_result = {
                    "timestamp": self._last_run,
                    "feed_update": feed_res,
                    "retired_stale_indicators": retired_count,
                    "status": "SUCCESS" if feed_res.get("status") in ["SUCCESS", "OFFLINE_FALLBACK"] else "FAILED"
                }

                # Emit actionable security notification if new threats ingested or offline fallback
                try:
                    records_added = feed_res.get("records_added", 0)
                    if feed_res.get("status") == "SUCCESS" and records_added > 0:
                        notification_service.create_notification(
                            db=db,
                            payload=NotificationCreate(
                                title="Threat Intelligence Signatures Updated",
                                message=f"Successfully synchronized {records_added} new verified malicious threat indicators from community feeds.",
                                severity="LOW",
                                category="THREAT_INTEL_SYNC",
                                target_domain="urlhaus-api.abuse.ch",
                                recommended_action="Dynamic network request shield updated automatically.",
                                source_component="THREAT_INTEL_SCHEDULER",
                                metadata_json={"records_added": records_added, "retired_count": retired_count}
                            )
                        )
                    elif feed_res.get("status") == "OFFLINE_FALLBACK":
                        notification_service.create_notification(
                            db=db,
                            payload=NotificationCreate(
                                title="Threat Feed Sync In Offline Safe Mode",
                                message="External threat intelligence feed was unreachable. Local cached threat database remains operational.",
                                severity="MEDIUM",
                                category="THREAT_INTEL_SYNC",
                                target_domain="urlhaus-api.abuse.ch",
                                recommended_action="Verify internet connection; local threat signatures remain fully active.",
                                source_component="THREAT_INTEL_SCHEDULER",
                                metadata_json={"status": "OFFLINE_FALLBACK", "error": feed_res.get("error")}
                            )
                        )
                except Exception as notif_err:
                    logger.debug(f"Non-critical notification emission warning: {notif_err}")

                self._last_result = cycle_result
                self._last_error = None
                self._runs_completed += 1
                self._calculate_next_run()
                return cycle_result
            except Exception as e:
                err_msg = str(e)
                logger.error(f"Threat intel sync cycle encountered error: {err_msg}", exc_info=True)
                self._last_error = err_msg
                self._calculate_next_run()
                try:
                    notification_service.create_notification(
                        db=db,
                        payload=NotificationCreate(
                            title="Threat Intel Sync Failure",
                            message=f"Threat intelligence synchronization cycle failed: {err_msg[:120]}",
                            severity="HIGH",
                            category="THREAT_INTEL_SYNC",
                            source_component="THREAT_INTEL_SCHEDULER",
                            recommended_action="Inspect backend logs and network connectivity."
                        )
                    )
                except Exception:
                    pass
                return {
                    "timestamp": self._last_run,
                    "status": "ERROR",
                    "error": err_msg
                }
            finally:
                db.close()

    async def _scheduler_loop(self):
        """Asynchronous background worker loop."""
        try:
            while self._running:
                sleep_seconds = self._interval_minutes * 60
                await asyncio.sleep(sleep_seconds)
                if not self._running:
                    break
                await self.run_sync_cycle()
        except asyncio.CancelledError:
            logger.debug("Threat intel scheduler loop received cancellation.")
        except Exception as e:
            self._status = "FAILED"
            self._last_error = str(e)
            logger.error(f"Threat intel scheduler loop crashed: {e}", exc_info=True)


# Singleton instance
threat_intel_scheduler = ThreatIntelScheduler()

