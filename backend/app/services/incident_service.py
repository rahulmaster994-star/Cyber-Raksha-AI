"""
backend/app/services/incident_service.py
Service layer orchestrating Stage 6 Incident Management and Phase B3 Unified Incident Correlation.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta
import random
import json
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.incident import SecurityIncident, IncidentAction, UserProtectionSetting
from app.models.security_event import SecurityEvent
from app.models.notification import Notification
from app.schemas.incident import (
    IncidentCreateRequest,
    IncidentUpdateRequest,
    IncidentDetailResponse,
    IncidentListResponse,
    IncidentActionSchema,
    ProtectionOverviewResponse
)
from ai_engine.prevention.prevention_engine import prevention_engine
from ai_engine.prevention.protection_rules import RESPONSE_PLAYBOOKS

SEVERITY_ORDER = {"LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}


class IncidentService:

    @classmethod
    def correlate_or_create_incident_from_event(
        cls,
        db: Session,
        source_component: str,
        event_type: str,
        severity: str,
        indicator: Optional[str],
        description: str,
        device_id: Optional[str] = None,
        detection_reason: Optional[str] = None
    ) -> SecurityIncident:
        """
        Phase B3: Correlates an incoming high-severity event into an existing active incident
        for the same threat indicator, or creates a new incident if none exists within 24h.
        """
        now = datetime.now(timezone.utc)
        clean_indicator = indicator.strip() if indicator else None

        # Look for existing active incident within 24 hours
        cutoff = now - timedelta(hours=24)
        existing = None
        if clean_indicator:
            inc_query = (
                db.query(SecurityIncident)
                .filter(
                    SecurityIncident.target_or_indicator == clean_indicator,
                    SecurityIncident.status.notin_(["RESOLVED", "CLOSED", "FALSE_POSITIVE"]),
                    SecurityIncident.created_at >= cutoff
                )
            )
            # Phase B3.1: Strict device isolation — correlate only within the SAME device scope
            if device_id:
                inc_query = inc_query.filter(SecurityIncident.device_id == device_id)
            else:
                inc_query = inc_query.filter(SecurityIncident.device_id.is_(None))

            existing = inc_query.first()

        if existing:
            # Correlate: upgrade severity if higher, add source component, update timestamp
            try:
                sources = json.loads(existing.source_components or "[]")
            except Exception:
                sources = []
            if source_component not in sources:
                sources.append(source_component)
            existing.source_components = json.dumps(sources)

            if SEVERITY_ORDER.get(severity.upper(), 1) > SEVERITY_ORDER.get(existing.severity.upper(), 1):
                existing.severity = severity.upper()

            # Append evidence reference
            try:
                evidence = json.loads(existing.evidence_references or "[]")
            except Exception:
                evidence = []
            evidence.append({
                "source": source_component,
                "event_type": event_type,
                "reason": detection_reason or description,
                "timestamp": now.isoformat()
            })
            existing.evidence_references = json.dumps(evidence)
            existing.updated_at = now

            db.commit()
            db.refresh(existing)
            return existing

        # Create new incident with collision-free incident number
        inc_number = f"CR-INC-{now.year}-{random.randint(1000, 9999)}"
        for _ in range(20):
            candidate = f"CR-INC-{now.year}-{random.randint(1000, 999999)}"
            if not db.query(SecurityIncident).filter(SecurityIncident.incident_number == candidate).first():
                inc_number = candidate
                break

        # Category mapping
        cat = "SUSPICIOUS_COMMUNICATION"
        if "URL" in event_type or "BROWSER" in source_component:
            cat = "MALICIOUS_WEBSITE"
        elif "SMS" in event_type or "OTP" in event_type:
            cat = "PHISHING"
        elif "CALL" in event_type:
            cat = "TELEPHONY_FRAUD"

        title = f"{severity.upper()} Threat Intercepted: {clean_indicator or event_type}"
        evidence_initial = [{
            "source": source_component,
            "event_type": event_type,
            "reason": detection_reason or description,
            "timestamp": now.isoformat()
        }]

        incident = SecurityIncident(
            incident_number=inc_number,
            category=cat,
            title=title,
            severity=severity.upper(),
            status="NEW",
            summary=description,
            target_or_indicator=clean_indicator,
            source_components=json.dumps([source_component]),
            device_id=device_id,
            evidence_references=json.dumps(evidence_initial),
            user_acknowledged=False,
            is_false_positive=False,
            created_at=now,
            updated_at=now
        )
        db.add(incident)
        db.commit()
        db.refresh(incident)

        # Attach guided containment playbooks
        pb = None
        if "PHISH" in cat or "MALICIOUS" in cat:
            pb = RESPONSE_PLAYBOOKS.get("PHISHING_CLICKED")
        elif "DIGITAL" in cat or "ARREST" in cat:
            pb = RESPONSE_PLAYBOOKS.get("DIGITAL_ARREST_EXTORTION")
        elif "FINANCIAL" in cat or "MONEY" in cat:
            pb = RESPONSE_PLAYBOOKS.get("MONEY_TRANSFERRED_SCAM")

        if pb:
            for step in pb.get("steps", []):
                action = IncidentAction(
                    incident_id=incident.id,
                    action_key=step.get("action_key", "ACTION"),
                    title=step.get("title", "Action Step"),
                    description=step.get("description", ""),
                    priority=step.get("priority", "IMMEDIATE"),
                    is_completed=False,
                    created_at=now
                )
                db.add(action)
            db.commit()
            db.refresh(incident)

        return incident

    @staticmethod
    def create_incident(request: IncidentCreateRequest, db: Session) -> IncidentDetailResponse:
        """Creates a security incident and automatically populates guided action playbooks."""
        now_year = datetime.now(timezone.utc).year
        inc_number = f"CR-INC-{now_year}-{random.randint(1000, 9999)}"
        for _ in range(20):
            candidate = f"CR-INC-{now_year}-{random.randint(1000, 999999)}"
            if not db.query(SecurityIncident).filter(SecurityIncident.incident_number == candidate).first():
                inc_number = candidate
                break
        now = datetime.now(timezone.utc)

        incident = SecurityIncident(
            incident_number=inc_number,
            category=request.category.upper(),
            title=request.title,
            severity=request.severity.upper(),
            status="ACTION_REQUIRED",
            summary=request.summary,
            related_analysis_id=request.related_analysis_id,
            evidence_references=request.evidence_references,
            created_at=now,
            updated_at=now
        )

        db.add(incident)
        db.commit()
        db.refresh(incident)

        # Populate playbook actions if matched or provided
        pb = None
        if request.playbook_id:
            pb = prevention_engine.get_playbook_by_id(request.playbook_id)

        if not pb:
            cat = request.category.upper()
            if "PHISH" in cat:
                pb = RESPONSE_PLAYBOOKS.get("PHISHING_CLICKED")
            elif "DIGITAL" in cat or "ARREST" in cat:
                pb = RESPONSE_PLAYBOOKS.get("DIGITAL_ARREST_EXTORTION")
            elif "VOICE" in cat or "AUDIO" in cat:
                pb = RESPONSE_PLAYBOOKS.get("VOICE_CLONING_IMPERSONATION")
            elif "FINANCIAL" in cat or "MONEY" in cat:
                pb = RESPONSE_PLAYBOOKS.get("MONEY_TRANSFERRED_SCAM")

        if pb:
            for step in pb.get("steps", []):
                action = IncidentAction(
                    incident_id=incident.id,
                    action_key=step.get("action_key", "ACTION"),
                    title=step.get("title", "Action Step"),
                    description=step.get("description", ""),
                    priority=step.get("priority", "IMMEDIATE"),
                    is_completed=False,
                    created_at=now
                )
                db.add(action)
            db.commit()
            db.refresh(incident)

        return IncidentService._format_incident(incident)

    @staticmethod
    def get_incidents(
        db: Session,
        limit: int = 50,
        status: Optional[str] = None,
        severity: Optional[str] = None,
        device_id: Optional[str] = None
    ) -> IncidentListResponse:
        """Retrieve incident history with optional status, severity, and device_id filters."""
        query = db.query(SecurityIncident)
        if status:
            query = query.filter(SecurityIncident.status == status.upper())
        if severity:
            query = query.filter(SecurityIncident.severity == severity.upper())
        if device_id:
            query = query.filter(SecurityIncident.device_id == device_id)
        incidents = query.order_by(desc(SecurityIncident.created_at)).limit(limit).all()

        formatted = [IncidentService._format_incident(inc) for inc in incidents]
        return IncidentListResponse(total_count=len(formatted), incidents=formatted)

    @staticmethod
    def get_incident_by_id(incident_id: int, db: Session) -> Optional[IncidentDetailResponse]:
        """Fetch incident detail and associated action items."""
        inc = db.query(SecurityIncident).filter(SecurityIncident.id == incident_id).first()
        if not inc:
            return None
        return IncidentService._format_incident(inc)

    @staticmethod
    def update_incident(incident_id: int, request: IncidentUpdateRequest, db: Session) -> Optional[IncidentDetailResponse]:
        """Update incident status and resolution notes."""
        inc = db.query(SecurityIncident).filter(SecurityIncident.id == incident_id).first()
        if not inc:
            return None

        now = datetime.now(timezone.utc)
        if request.status:
            inc.status = request.status.upper()
            if inc.status in ["RESOLVED", "CLOSED"]:
                inc.resolved_at = now
        if request.resolution_notes:
            inc.resolution_notes = request.resolution_notes

        inc.updated_at = now
        db.commit()
        db.refresh(inc)
        return IncidentService._format_incident(inc)

    @staticmethod
    def acknowledge_incident(incident_id: int, db: Session, user_or_device: Optional[str] = None, notes: Optional[str] = None) -> Optional[IncidentDetailResponse]:
        """User marks incident as seen/acknowledged; transitions NEW -> INVESTIGATING."""
        inc = db.query(SecurityIncident).filter(SecurityIncident.id == incident_id).first()
        if not inc:
            return None

        now = datetime.now(timezone.utc)
        inc.user_acknowledged = True
        inc.acknowledged_at = now
        if inc.status == "NEW":
            inc.status = "INVESTIGATING"
        if notes:
            inc.summary = f"{inc.summary} | [ACK by {user_or_device or 'user'}]: {notes}"
        inc.updated_at = now

        db.commit()
        db.refresh(inc)
        return IncidentService._format_incident(inc)

    @staticmethod
    def resolve_incident(incident_id: int, resolution_notes: str, db: Session, user_or_device: Optional[str] = None) -> Optional[IncidentDetailResponse]:
        """Resolves an incident with audit notes."""
        inc = db.query(SecurityIncident).filter(SecurityIncident.id == incident_id).first()
        if not inc:
            return None

        now = datetime.now(timezone.utc)
        inc.status = "RESOLVED"
        inc.resolved_at = now
        inc.resolution_notes = f"[Resolved by {user_or_device or 'analyst'}]: {resolution_notes}"
        inc.updated_at = now

        db.commit()
        db.refresh(inc)
        return IncidentService._format_incident(inc)

    @staticmethod
    def dispute_incident(
        incident_id: int,
        reason: str,
        db: Session,
        user_or_device: Optional[str] = None
    ) -> Optional[IncidentDetailResponse]:
        """
        Phase B3.1: Records a user dispute against an incident.
        Preserves all existing threat evidence and incident history.
        Does NOT alter or erase global authoritative threat intelligence.
        """
        inc = db.query(SecurityIncident).filter(SecurityIncident.id == incident_id).first()
        if not inc:
            return None

        now = datetime.now(timezone.utc)
        inc.status = "DISPUTED"

        # Append dispute record to evidence_references
        try:
            evidence = json.loads(inc.evidence_references or "[]")
        except Exception:
            evidence = []
        evidence.append({
            "action": "USER_DISPUTE",
            "actor": user_or_device or "user",
            "reason": reason,
            "timestamp": now.isoformat()
        })
        inc.evidence_references = json.dumps(evidence)
        inc.summary = f"{inc.summary} | [DISPUTED by {user_or_device or 'user'}]: {reason}"
        inc.updated_at = now

        db.commit()
        db.refresh(inc)
        return IncidentService._format_incident(inc)

    @staticmethod
    def mark_false_positive(
        incident_id: int,
        reason: str,
        db: Session,
        user_or_device: Optional[str] = None,
        is_admin: bool = False
    ) -> Optional[IncidentDetailResponse]:
        """
        Phase B3.1: Marks incident as false positive and closes it.
        If indicator is authoritative (e.g. URLhaus, CERT_IN) and caller is NOT admin,
        only the local incident is marked, leaving global authoritative intelligence intact.
        If caller is admin, global ThreatIndicator can be deactivated.
        """
        inc = db.query(SecurityIncident).filter(SecurityIncident.id == incident_id).first()
        if not inc:
            return None

        now = datetime.now(timezone.utc)
        inc.status = "FALSE_POSITIVE"
        inc.is_false_positive = True
        inc.resolved_at = now
        role_label = "admin" if is_admin else "user"
        inc.resolution_notes = f"[False Positive adjudicated by {user_or_device or role_label} ({role_label})]: {reason}"
        inc.updated_at = now

        # Only an authorized admin can deactivate global authoritative threat indicators
        if is_admin and inc.target_or_indicator:
            from app.models.threat_intel import ThreatIndicator
            ioc = db.query(ThreatIndicator).filter(
                ThreatIndicator.indicator_value == inc.target_or_indicator
            ).first()
            if ioc:
                ioc.is_active = False

        db.commit()
        db.refresh(inc)
        return IncidentService._format_incident(inc)

    @staticmethod
    def complete_action(action_id: int, db: Session) -> Optional[IncidentActionSchema]:
        """Mark a user-selected containment action as completed."""
        action = db.query(IncidentAction).filter(IncidentAction.id == action_id).first()
        if not action:
            return None

        action.is_completed = True
        action.completed_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(action)

        inc = db.query(SecurityIncident).filter(SecurityIncident.id == action.incident_id).first()
        if inc:
            remaining = db.query(IncidentAction).filter(
                IncidentAction.incident_id == inc.id,
                IncidentAction.is_completed == False
            ).count()
            if remaining == 0 and inc.status != "CLOSED":
                inc.status = "CONTAINMENT_IN_PROGRESS"
                db.commit()

        return IncidentActionSchema(
            id=action.id,
            action_key=action.action_key,
            title=action.title,
            description=action.description,
            priority=action.priority,
            is_completed=action.is_completed,
            completed_at=action.completed_at.isoformat() if action.completed_at else None,
            created_at=action.created_at.isoformat()
        )

    @staticmethod
    def get_protection_overview(db: Session) -> ProtectionOverviewResponse:
        """Returns statistics for the Personal Protection Center."""
        all_incidents = db.query(SecurityIncident).all()
        active_count = sum(1 for i in all_incidents if i.status not in ["RESOLVED", "CLOSED", "FALSE_POSITIVE"])
        resolved_count = sum(1 for i in all_incidents if i.status in ["RESOLVED", "CLOSED", "FALSE_POSITIVE"])

        all_actions = db.query(IncidentAction).all()
        pending_actions = sum(1 for a in all_actions if not a.is_completed)
        completed_actions = sum(1 for a in all_actions if a.is_completed)

        deductions = (active_count * 15) + (pending_actions * 5)
        posture_score = max(20.0, min(100.0, 100.0 - deductions))

        recent = (
            db.query(SecurityIncident)
            .order_by(desc(SecurityIncident.created_at))
            .limit(5)
            .all()
        )

        return ProtectionOverviewResponse(
            active_incidents_count=active_count,
            resolved_incidents_count=resolved_count,
            pending_actions_count=pending_actions,
            completed_actions_count=completed_actions,
            security_posture_score=round(posture_score, 1),
            recent_incidents=[IncidentService._format_incident(i) for i in recent],
            available_playbooks_count=len(RESPONSE_PLAYBOOKS),
            privacy_mode="STRICT_LOCAL_ONLY"
        )

    @staticmethod
    def _format_incident(inc: SecurityIncident) -> IncidentDetailResponse:
        formatted_actions = [
            IncidentActionSchema(
                id=a.id,
                action_key=a.action_key,
                title=a.title,
                description=a.description,
                priority=a.priority,
                is_completed=a.is_completed,
                completed_at=a.completed_at.isoformat() if a.completed_at else None,
                created_at=a.created_at.isoformat()
            )
            for a in inc.actions
        ]

        try:
            sources = json.loads(inc.source_components or "[]")
        except Exception:
            sources = []

        return IncidentDetailResponse(
            id=inc.id,
            incident_number=inc.incident_number,
            category=inc.category,
            title=inc.title,
            severity=inc.severity,
            status=inc.status,
            summary=inc.summary,
            target_or_indicator=inc.target_or_indicator,
            source_components=sources,
            device_id=inc.device_id,
            user_acknowledged=inc.user_acknowledged or False,
            acknowledged_at=inc.acknowledged_at.isoformat() if inc.acknowledged_at else None,
            is_false_positive=inc.is_false_positive or False,
            related_analysis_id=inc.related_analysis_id,
            evidence_references=inc.evidence_references,
            resolution_notes=inc.resolution_notes,
            resolved_at=inc.resolved_at.isoformat() if inc.resolved_at else None,
            created_at=inc.created_at.isoformat(),
            updated_at=inc.updated_at.isoformat(),
            actions=formatted_actions
        )
