"""
backend/app/services/threat_intel_service.py
Service layer for Threat Intelligence searches, feed updates, live event logging,
and unified multi-vector risk assessment.
"""
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.threat_intel import ThreatIndicator, ThreatFeedLog, UnifiedRiskRecord
from app.models.security_event import SecurityEvent
from app.models.notification import Notification
from app.schemas.threat_intel import (
    ThreatSearchResponse,
    ThreatIndicatorSchema,
    ThreatIntelStatusResponse,
    UnifiedAnalyzeResponse,
    LiveThreatEvent
)
from ai_engine.threat_intelligence.threat_database import (
    lookup_indicator,
    get_intel_stats,
    get_all_indicators
)
from ai_engine.threat_intelligence.feed_updater import feed_updater
from ai_engine.threat_intelligence.intelligence_engine import intelligence_engine
from ai_engine.threat_intelligence.indicator_extractor import extract_indicators


class ThreatIntelService:
    @staticmethod
    def search_indicator(query: str, indicator_type: Optional[str] = None) -> ThreatSearchResponse:
        """
        Searches query against verified threat cache. Auto-detects type if omitted.
        """
        clean_q = query.strip()
        t = indicator_type

        if not t:
            if clean_q.startswith(("http://", "https://")):
                t = "URL"
            elif any(c.isalpha() for c in clean_q) and "." in clean_q:
                t = "DOMAIN"
            elif any(c.isdigit() for c in clean_q) and clean_q.count(".") == 3:
                t = "IP"
            else:
                t = "URL"

        match = lookup_indicator(t, clean_q)

        # Fallback: if user searched URL as domain or vice versa
        if not match and t == "URL" and "://" in clean_q:
            from urllib.parse import urlparse
            try:
                host = urlparse(clean_q).hostname
                if host:
                    match = lookup_indicator("DOMAIN", host)
                    if match:
                        t = "DOMAIN"
            except Exception:
                pass

        if match:
            schema = ThreatIndicatorSchema(
                indicator_type=match.get("indicator_type", t),
                indicator_value=match.get("indicator_value", clean_q),
                threat_type=match.get("threat_type", "MALICIOUS"),
                severity=match.get("severity", "HIGH"),
                confidence_score=match.get("confidence_score", 0.9),
                source_name=match.get("source_name", "THREAT_INTEL"),
                source_reference=match.get("source_reference"),
                description=match.get("description"),
                is_active=match.get("is_active", True)
            )
            return ThreatSearchResponse(
                query=clean_q,
                indicator_type=t,
                is_threat_found=True,
                matched_indicator=schema,
                source=match.get("source_name"),
                severity=match.get("severity"),
                search_timestamp=datetime.now(timezone.utc).isoformat()
            )

        return ThreatSearchResponse(
            query=clean_q,
            indicator_type=t,
            is_threat_found=False,
            matched_indicator=None,
            source=None,
            severity="LOW",
            search_timestamp=datetime.now(timezone.utc).isoformat()
        )

    @staticmethod
    def get_status() -> ThreatIntelStatusResponse:
        """Fetch threat intelligence system status and database telemetry."""
        from app.services.threat_intel_scheduler import threat_intel_scheduler
        from app.core.config import settings

        stats = get_intel_stats()
        sched_telemetry = threat_intel_scheduler.get_telemetry()

        return ThreatIntelStatusResponse(
            module="THREAT_INTEL",
            engine_stage="STAGE_5",
            service_status="OPERATIONAL",
            total_active_indicators=stats["total_active_indicators"],
            by_type=stats["by_type"],
            sources=stats["sources"],
            last_feed_update=feed_updater.last_update,
            feed_updater_status=feed_updater.last_status,
            auto_sync_enabled=settings.THREAT_INTEL_AUTO_SYNC_ENABLED,
            sync_interval_minutes=sched_telemetry.get("sync_interval_minutes", settings.THREAT_INTEL_SYNC_INTERVAL_MINUTES),
            next_scheduled_sync=sched_telemetry.get("next_run"),
            scheduler_status=sched_telemetry.get("status", "IDLE")
        )

    @staticmethod
    def trigger_feed_update(db: Session) -> Dict[str, Any]:
        """Manually trigger threat feed pull from URLhaus and log to database."""
        result = feed_updater.update_urlhaus_feed()

        # Log feed update to database
        feed_log = ThreatFeedLog(
            source_name=result.get("source", "URLHAUS"),
            status=result.get("status", "SUCCESS"),
            records_added=result.get("records_added", 0),
            duration_seconds=result.get("duration_seconds", 0.0),
            error_message=result.get("error")
        )
        try:
            db.add(feed_log)
            db.commit()
        except Exception:
            db.rollback()

        # Update Stage 9 Threat Intel Operations Telemetry
        try:
            from app.services.threat_intel_ops import threat_intel_ops
            threat_intel_ops.record_update_result(
                source_key="URLHAUS",
                success=result.get("status") == "SUCCESS",
                records_added=result.get("records_added", 0),
                records_updated=0,
                records_rejected=0,
                error_message=result.get("error")
            )
        except Exception:
            pass

        return result

    @staticmethod
    def get_verified_indicators(limit: int = 50, active_only: bool = True) -> List[ThreatIndicatorSchema]:
        """Retrieve verified IOC list."""
        iocs = get_all_indicators(limit, active_only=active_only)
        return [
            ThreatIndicatorSchema(
                indicator_type=item.get("indicator_type", "URL"),
                indicator_value=item.get("indicator_value", ""),
                threat_type=item.get("threat_type", "PHISHING"),
                severity=item.get("severity", "HIGH"),
                confidence_score=item.get("confidence_score", 0.95),
                source_name=item.get("source_name", "UNKNOWN"),
                source_reference=item.get("source_reference"),
                description=item.get("description"),
                is_active=item.get("is_active", True)
            )
            for item in iocs
        ]

    @staticmethod
    def retire_stale_indicators(max_age_days: int = 30) -> int:
        """Retires cached indicators older than max_age_days."""
        from ai_engine.threat_intelligence.threat_database import retire_stale_indicators
        return retire_stale_indicators(max_age_days=max_age_days)

    @staticmethod
    def analyze_unified(
        db: Session,
        url: Optional[str] = None,
        message: Optional[str] = None,
        is_digital_arrest: bool = False,
        audio_bytes: Optional[bytes] = None,
        audio_filename: Optional[str] = None
    ) -> UnifiedAnalyzeResponse:
        """
        Executes multi-module unified risk analysis and logs SecurityEvents and Notifications.
        """
        # Execute central intelligence engine
        res = intelligence_engine.analyze_unified(
            url=url,
            message=message,
            is_digital_arrest=is_digital_arrest,
            audio_bytes=audio_bytes,
            audio_filename=audio_filename
        )

        # 1. Log to UnifiedRiskRecord table
        target_summary = url or (message[:80] if message else "Audio Sample")
        modules_list = [k for k, v in res["modules"].items() if v is not None]

        risk_record = UnifiedRiskRecord(
            submission_type="MULTI_MODAL" if len(modules_list) > 1 else "SINGLE_VECTOR",
            target_summary=target_summary[:255],
            overall_risk_level=res["overall_risk_level"],
            overall_risk_score=res["overall_risk_score"],
            threat_category=res["threat_category"],
            corroboration_factor=1.25 if res["is_corroborated"] else 1.0,
            modules_involved=",".join(modules_list),
            intelligence_matches_count=res["intel_matches_count"],
            explanation=res["explanation"],
            recommended_action=" | ".join(res["recommended_actions"]),
            evidence_json=json.dumps({
                "corroboration_notes": res["corroboration_notes"],
                "intel_matches": res["intel_matches"]
            })
        )

        # 2. Trigger SecurityEvent if HIGH or CRITICAL
        if res["overall_risk_level"] in ["HIGH", "CRITICAL"]:
            sec_event = SecurityEvent(
                event_type="UNIFIED_THREAT_DETECTION",
                severity=res["overall_risk_level"],
                source_component="UNIFIED_RISK_ENGINE",
                description=f"High risk threat detected: {res['threat_category']} ({res['overall_risk_score']}/100)",
                raw_payload=json.dumps({"target": target_summary, "level": res["overall_risk_level"]})
            )
            # Create analyst notification
            notif = Notification(
                title=f"{res['overall_risk_level']} Alert: {res['threat_category']}",
                message=f"Threat score {res['overall_risk_score']}/100 on {target_summary[:60]}",
                notification_type=res["overall_risk_level"],
                recipient_role="analyst"
            )
            try:
                db.add(sec_event)
                db.add(notif)
            except Exception:
                pass

        try:
            db.add(risk_record)
            db.commit()
        except Exception:
            db.rollback()

        return UnifiedAnalyzeResponse(**res)

    @staticmethod
    def get_live_events(db: Session, limit: int = 20) -> List[LiveThreatEvent]:
        """Fetch recent security events logged across the platform."""
        events = (
            db.query(SecurityEvent)
            .order_by(desc(SecurityEvent.created_at))
            .limit(limit)
            .all()
        )
        return [
            LiveThreatEvent(
                id=e.id,
                event_type=e.event_type,
                severity=e.severity,
                source_component=e.source_component,
                description=e.description,
                created_at=e.created_at.isoformat()
            )
            for e in events
        ]

