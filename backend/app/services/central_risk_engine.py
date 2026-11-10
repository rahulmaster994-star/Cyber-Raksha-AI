"""
Cyber Raksha AI - Central Security Risk Engine
Phase B3: Unified Protection Integration

Correlates security signals across Browser Protection, Native Android App,
and Automated Threat Intelligence to produce evidence-based, explainable,
and non-duplicative risk assessments and incident management.
"""
import hashlib
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.security_event import SecurityEvent
from app.models.threat_intel import ThreatIndicator
from app.models.phone_reputation import PhoneReputation
from app.models.incident import SecurityIncident
from app.schemas.security_event import (
    SecurityEventCreate,
    SecurityEventResponse,
    UnifiedRiskEvaluationRequest,
    UnifiedRiskEvaluationResponse
)
from app.schemas.notification import NotificationCreate
from app.services.notification_service import notification_service
from app.services.phone_reputation_service import phone_reputation_service
from app.services.sms_analysis_service import sms_analysis_service
from app.utils.helpers import normalize_threat_indicator

logger = logging.getLogger("cyber_raksha.risk_engine")

AUTHORITATIVE_SOURCES = {
    # Web, Phishing & Malware Feeds
    "URLHAUS",
    "PHISHTANK",
    "GOOGLE_SAFE_BROWSING",
    "VERIFIED_THREAT_INTEL",
    "ADMIN_VERIFIED",
    # Regulatory & National Cybersecurity Authorities
    "GOV_DATABASE",
    "CERT_IN",
    "TRAI_REGISTRY",
    "CYBER_CRIME_PORTAL",
}

CORRELATION_WINDOW_HOURS = 24
EVENT_DEDUPLICATION_WINDOW_SECONDS = 30.0
SEVERITY_ORDER = {"SAFE": 0, "INFO": 1, "LOW": 2, "MEDIUM": 3, "HIGH": 4, "CRITICAL": 5}


class CentralSecurityRiskEngine:
    """
    Unified correlation and risk synthesis engine connecting all Cyber Raksha AI components.
    """

    @staticmethod
    def _compute_event_hash(source_component: str, event_type: str, indicator: Optional[str], device_id: Optional[str] = None) -> str:
        clean_ind = normalize_threat_indicator(indicator) or ""
        dev = (device_id or "").strip()
        raw = f"{dev}:{source_component}:{event_type}:{clean_ind.lower()}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def process_security_event(self, db: Session, payload: SecurityEventCreate) -> SecurityEvent:
        """
        Ingests, validates, deduplicates, and evaluates an incoming security event.
        Correlates with threat intelligence and incident management.
        Guarantees deterministic indicator normalization, device isolation, and authoritative source validation.
        """
        now = datetime.now(timezone.utc)
        clean_indicator = normalize_threat_indicator(payload.threat_indicator) if payload.threat_indicator else None
        event_hash = self._compute_event_hash(payload.source_component, payload.event_type, clean_indicator, payload.device_id)

        # 1. Deduplication check: suppress identical events from the SAME component & device within 30-second window
        recent_cutoff = now - timedelta(seconds=EVENT_DEDUPLICATION_WINDOW_SECONDS)
        dup_query = (
            db.query(SecurityEvent)
            .filter(
                SecurityEvent.event_hash == event_hash,
                SecurityEvent.source_component == payload.source_component,
                SecurityEvent.created_at >= recent_cutoff
            )
        )
        if payload.device_id:
            dup_query = dup_query.filter(SecurityEvent.device_id == payload.device_id)
        else:
            dup_query = dup_query.filter(SecurityEvent.device_id.is_(None))

        dup = dup_query.first()
        if dup:
            logger.info(f"Deduplicated event from {payload.source_component} for {clean_indicator}")
            return dup

        # 2. Risk Evaluation & Threat Intel Correlation (Phase B3.1 Security Closure)
        # All client-supplied confidence scores and authority claims are treated as UNTRUSTED.
        raw_sev = payload.severity.upper()
        evaluated_sev = raw_sev
        evaluated_score = min(max(payload.risk_score, 0.0), 100.0)
        corroboration_notes = []
        is_corroborated_authority = False

        if clean_indicator:
            # Check Verified Authoritative Threat Intelligence Database
            intel_match = (
                db.query(ThreatIndicator)
                .filter(
                    (ThreatIndicator.indicator_value == clean_indicator) |
                    (ThreatIndicator.indicator_value.like(f"%{clean_indicator}%"))
                )
                .first()
            )
            if intel_match and intel_match.is_active:
                # Strictly require authoritative feed source; high numerical confidence alone does NOT establish authority
                is_corroborated_authority = intel_match.source_name in AUTHORITATIVE_SOURCES
                corroboration_notes.append(
                    f"Corroborated by verified threat feed ({intel_match.source_name}): {intel_match.threat_type} ({intel_match.severity})"
                )
                if SEVERITY_ORDER.get(intel_match.severity, 0) > SEVERITY_ORDER.get(evaluated_sev, 0):
                    evaluated_sev = intel_match.severity
                    evaluated_score = max(evaluated_score, intel_match.confidence_score * 100.0)

        # Authoritative Source Guard: A client CANNOT unilaterally force a CRITICAL classification
        # or forge an authoritative source. Escalation to CRITICAL strictly requires verified backend authority.
        if evaluated_sev == "CRITICAL" and not is_corroborated_authority:
            evaluated_sev = "HIGH"
            corroboration_notes.append(
                "Unverified client CRITICAL claim capped at HIGH: authoritative feed verification required for CRITICAL escalation."
            )

        # 3. Create or Correlate into Incident
        incident = None
        if evaluated_sev in {"HIGH", "CRITICAL"}:
            from app.services.incident_service import IncidentService
            incident = IncidentService.correlate_or_create_incident_from_event(
                db=db,
                source_component=payload.source_component,
                event_type=payload.event_type,
                severity=evaluated_sev,
                indicator=clean_indicator,
                description=payload.description,
                device_id=payload.device_id,
                detection_reason=payload.detection_reason
            )

        # 4. Persist SecurityEvent record
        reason_text = payload.detection_reason or payload.description
        if corroboration_notes:
            reason_text = f"{reason_text} | {' | '.join(corroboration_notes)}"

        verification_status = "CORROBORATED" if is_corroborated_authority else "UNVERIFIED"

        sec_event = SecurityEvent(
            event_type=payload.event_type,
            severity=evaluated_sev,
            source_component=payload.source_component,
            device_id=payload.device_id,
            threat_indicator=clean_indicator,
            risk_score=evaluated_score,
            detection_reason=reason_text,
            source_ip=payload.source_ip,
            description=payload.description,
            raw_payload=payload.raw_payload,
            verification_status=verification_status,
            incident_id=incident.id if incident else None,
            processing_status="CORRELATED" if incident else "PROCESSED",
            event_hash=event_hash,
            created_at=now
        )
        db.add(sec_event)
        db.commit()
        db.refresh(sec_event)

        # 5. Unified Notification Dispatch (Severity-based orchestration with suppression)
        if evaluated_sev in {"HIGH", "CRITICAL"}:
            notif_title = f"{evaluated_sev} Security Threat: {clean_indicator or payload.event_type}"
            notif_category = "MALICIOUS_WEBSITE" if "URL" in payload.event_type or "BROWSER" in payload.source_component else "SECURITY_ALERT"

            notif_msg = f"Threat detected by {payload.source_component}: {reason_text}"
            if incident:
                notif_msg += f" (Incident {incident.incident_number})"

            notif = NotificationCreate(
                title=notif_title,
                message=notif_msg,
                severity=evaluated_sev,
                category=notif_category,
                target_domain=clean_indicator,
                recommended_action="Navigation or communication blocked. Review incident details.",
                source_component=payload.source_component,
                metadata_json={
                    "event_id": sec_event.event_id,
                    "incident_id": incident.id if incident else None,
                    "device_id": payload.device_id,
                    "threat_indicator": clean_indicator
                }
            )
            try:
                notification_service.create_notification(db, notif)
            except Exception as e:
                logger.warning(f"Notification dispatch notice: {e}")

        return sec_event

    def evaluate_risk(self, db: Session, req: UnifiedRiskEvaluationRequest) -> UnifiedRiskEvaluationResponse:
        """
        Evaluates risk across multiple data sources without double-counting.
        Correlates threat intelligence, caller reputation, and known IOCs.
        """
        now = datetime.now(timezone.utc)
        indicator = req.indicator.strip()
        ind_type = req.indicator_type.upper()
        sources = [req.source_component]
        reasons = []
        is_verified = False
        risk_level = "LOW"
        risk_score = 10.0
        confidence = 0.50
        fraud_cat = None
        classification = "UNKNOWN"
        intelligence_status = "NOT_CONFIRMED"
        evidence_items: List[Dict[str, Any]] = []

        if ind_type in {"URL", "DOMAIN"}:
            clean_dom = indicator.replace("http://", "").replace("https://", "").split("/")[0].lower()
            ioc = (
                db.query(ThreatIndicator)
                .filter(
                    (ThreatIndicator.indicator_value == indicator) |
                    (ThreatIndicator.indicator_value == clean_dom) |
                    (ThreatIndicator.indicator_value.like(f"%{clean_dom}%"))
                )
                .first()
            )
            if ioc and ioc.is_active:
                sources.append(ioc.source_name)
                is_verified = ioc.source_name in AUTHORITATIVE_SOURCES
                risk_level = ioc.severity
                risk_score = 95.0 if ioc.severity == "CRITICAL" else 80.0
                confidence = ioc.confidence_score
                fraud_cat = ioc.threat_type
                classification = ioc.threat_type or "PHISHING"
                intelligence_status = "CONFIRMED_MALICIOUS" if is_verified else "UNVERIFIED_THREAT"
                reasons.append(f"Destination flagged in verified threat feed ({ioc.source_name}): {ioc.description}")
                evidence_items.append({
                    "type": "AUTHORITATIVE_INTEL",
                    "description": f"Indexed by {ioc.source_name} ({ioc.threat_type})",
                    "risk_contribution": risk_score
                })
            else:
                # Phase B4: Intelligent Machine Learning & Brand Impersonation Inspection
                brand_match = None
                try:
                    from ai_engine.core.brand_impersonation import check_brand_impersonation
                    brand_match = check_brand_impersonation(clean_dom)
                    if brand_match:
                        sources.append("BRAND_IMPERSONATION_DETECTOR")
                        evidence_items.append({
                            "type": "DOMAIN_IMPERSONATION",
                            "description": brand_match["description"],
                            "risk_contribution": brand_match["risk_contribution"]
                        })
                        reasons.append(brand_match["description"])
                        risk_score += brand_match["risk_contribution"]
                        fraud_cat = "BRAND_IMPERSONATION"
                        classification = "POSSIBLE_PHISHING"
                except Exception:
                    pass

                try:
                    from ai_engine.inference.phishing_detector import detect_phishing
                    ml_res = detect_phishing(indicator)
                    if ml_res.success:
                        sources.append(f"ML_CLASSIFIER ({ml_res.model_version})")
                        if ml_res.classification in ["PHISHING", "SUSPICIOUS"]:
                            risk_score = max(risk_score, ml_res.risk_score)
                            confidence = ml_res.confidence
                            classification = "POSSIBLE_PHISHING" if ml_res.classification == "PHISHING" else "SUSPICIOUS"
                            intelligence_status = "UNVERIFIED_HEURISTIC"
                            for ind in ml_res.analysis.get("risk_indicators", []):
                                if ind not in reasons:
                                    reasons.append(ind)
                                    evidence_items.append({
                                        "type": "HEURISTIC_INDICATOR",
                                        "description": ind,
                                        "risk_contribution": 10.0
                                    })
                        else:
                            if not brand_match:
                                risk_score = min(risk_score, 10.0)
                                classification = "BENIGN"
                                intelligence_status = "NOT_CONFIRMED"
                                confidence = ml_res.confidence
                                reasons.append("Structural and machine learning evaluation indicates normal benign profile.")
                except Exception:
                    pass

                # Derive calibrated risk level (unverified heuristics capped at HIGH per Objective 1)
                if risk_score >= 75.0:
                    risk_level = "HIGH"
                elif risk_score >= 45.0:
                    risk_level = "MEDIUM"
                elif risk_score >= 20.0:
                    risk_level = "LOW"
                else:
                    risk_level = "SAFE"

        elif ind_type in {"PHONE_NUMBER", "CALLER"}:
            rep = phone_reputation_service.check_number(db, indicator)
            risk_level = rep["risk_level"]
            confidence = rep["confidence_score"]
            fraud_cat = rep["fraud_category"]
            classification = rep["fraud_category"] or "UNKNOWN"
            risk_score = 90.0 if risk_level == "CRITICAL" else (70.0 if risk_level == "HIGH" else (40.0 if risk_level == "MEDIUM" else 5.0))
            is_verified = rep["is_verified_authority"]
            intelligence_status = "CONFIRMED_MALICIOUS" if is_verified else "UNVERIFIED_HEURISTIC"
            sources.append(rep["source"])
            reasons.append(rep["classification_reason"])
            evidence_items.append({
                "type": "CALLER_REPUTATION",
                "description": rep["classification_reason"],
                "risk_contribution": risk_score
            })

        elif ind_type in {"SMS", "SMS_CONTENT", "MESSAGE"}:
            sms_res = sms_analysis_service.analyze_sms(
                db=db,
                device_id=req.device_id or "anonymous",
                message_text=indicator,
                sender=req.context_data.get("sender") if req.context_data else None
            )
            has_malicious_link = any(t.get("is_malicious") for t in sms_res.get("url_threats", []))
            risk_level = sms_res["risk_level"]
            risk_score = sms_res["risk_score"]
            confidence = 0.90 if has_malicious_link else (0.80 if sms_res["risk_score"] > 60 else 0.55)
            fraud_cat = sms_res["fraud_category"]
            classification = sms_res["fraud_category"]
            reasons = sms_res["detection_reasons"]
            intelligence_status = "CONFIRMED_MALICIOUS" if has_malicious_link else "UNVERIFIED_HEURISTIC"
            sources.append("SMS_FRAUD_ENGINE")
            for r in reasons:
                evidence_items.append({"type": "MESSAGE_FRAUD_PATTERN", "description": r, "risk_contribution": 15.0})

        # Deduplicate sources
        unique_sources = list(dict.fromkeys(sources))

        # Check for active incident
        active_incident = (
            db.query(SecurityIncident)
            .filter(
                SecurityIncident.target_or_indicator == indicator,
                SecurityIncident.status.notin_(["RESOLVED", "CLOSED", "FALSE_POSITIVE"])
            )
            .first()
        )

        action = (
            "Do not enter credentials, authorize payments, or follow embedded links."
            if risk_level in {"HIGH", "CRITICAL"}
            else ("Exercise caution. Verify destination identity via independent official channels." if risk_level == "MEDIUM" else "Proceed with normal caution.")
        )

        return UnifiedRiskEvaluationResponse(
            indicator=indicator,
            indicator_type=ind_type,
            risk_level=risk_level,
            risk_score=min(100.0, max(0.0, round(risk_score, 1))),
            confidence_score=round(confidence, 2),
            fraud_category=fraud_cat,
            detection_reasons=reasons,
            corroborating_sources=unique_sources,
            is_verified_threat=is_verified,
            recommended_action=action,
            incident_id=active_incident.id if active_incident else None,
            evaluated_at=now,
            classification=classification,
            intelligence_status=intelligence_status,
            evidence_items=evidence_items
        )


central_risk_engine = CentralSecurityRiskEngine()

