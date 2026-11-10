"""
Cyber Raksha AI - Hardened Phone Reputation Service
Phase B2 & B2.1: Intelligent Call Fraud Protection & Robust Reputation Modeling
"""
import hashlib
import json
import re
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from app.models.phone_reputation import PhoneReputation

AUTHORITATIVE_SOURCES = {
    "GOV_DATABASE",
    "CERT_IN",
    "TRAI_REGISTRY",
    "CYBER_CRIME_PORTAL",
    "VERIFIED_THREAT_INTEL",
    "ADMIN_VERIFIED"
}


class PhoneReputationService:
    @staticmethod
    def normalize_number(raw: str) -> str:
        """
        Normalizes a phone number into standardized international or digit format.
        Removes spaces, dashes, parentheses, dots.
        Preserves leading '+' if present.
        """
        if not raw:
            return ""
        trimmed = raw.strip()
        has_plus = trimmed.startswith("+")
        digits_only = re.sub(r"\D", "", trimmed)

        if not digits_only:
            return raw.strip()

        # Handle Indian 10-digit standard mobile formatting
        if len(digits_only) == 10:
            return f"+91{digits_only}"
        elif len(digits_only) == 11 and digits_only.startswith("0"):
            return f"+91{digits_only[1:]}"
        elif len(digits_only) == 12 and digits_only.startswith("91"):
            return f"+{digits_only}"

        if has_plus:
            return f"+{digits_only}"
        return digits_only

    @classmethod
    def check_number(cls, db: Session, raw_number: str) -> Dict[str, Any]:
        """
        Checks a phone number against local fraud intelligence repository.
        Evaluates temporal decay and returns genuine UNKNOWN if not in database (never fakes reputation).
        """
        normalized = cls.normalize_number(raw_number)
        now = datetime.now(timezone.utc)

        record = (
            db.query(PhoneReputation)
            .filter((PhoneReputation.phone_number == normalized) | (PhoneReputation.phone_number == raw_number.strip()))
            .first()
        )

        if record:
            # Apply temporal reputation decay for community-sourced entries
            cls._apply_reputation_decay(record, now)
            db.commit()

            action = cls._get_recommended_action(record.risk_level, record.fraud_category, record.is_verified_authority)
            return {
                "phone_number": raw_number,
                "normalized_number": normalized,
                "risk_level": record.risk_level,
                "fraud_category": record.fraud_category,
                "report_count": record.report_count,
                "confidence_score": record.confidence_score,
                "source": record.source,
                "is_verified_authority": record.is_verified_authority,
                "classification_reason": record.classification_reason or "Reported via Cyber Raksha community defense.",
                "dispute_count": record.dispute_count,
                "notes": record.notes,
                "recommended_action": action,
                "checked_at": now
            }

        # Safe fallback: UNKNOWN (Always Fail-Open)
        return {
            "phone_number": raw_number,
            "normalized_number": normalized,
            "risk_level": "UNKNOWN",
            "fraud_category": None,
            "report_count": 0,
            "confidence_score": 0.0,
            "source": "CYBER_RAKSHA_INTEL",
            "is_verified_authority": False,
            "classification_reason": "No adverse history recorded for this number.",
            "dispute_count": 0,
            "notes": "No fraudulent history reported for this number.",
            "recommended_action": "Unverified caller. Never share OTPs, PINs, or transfer money under pressure.",
            "checked_at": now
        }

    @classmethod
    def report_number(
        cls,
        db: Session,
        raw_number: str,
        reporting_device_id: Optional[str] = None,
        fraud_category: Optional[str] = None,
        notes: Optional[str] = None,
        is_authority: bool = False,
        source: Optional[str] = None
    ) -> PhoneReputation:
        """
        Records or updates threat reports for a phone number with strict Sybil attack resistance:
        - Tracks distinct reporting device hashes.
        - Repeated reports from the same device update metadata without inflating report count.
        - Community reports alone can NEVER escalate to CRITICAL (auto-blocking).
        - CRITICAL is strictly reserved for verified authoritative intelligence.
        """
        normalized = cls.normalize_number(raw_number)
        now = datetime.now(timezone.utc)
        cat = (fraud_category or "TELEMARKETING").upper()

        record = (
            db.query(PhoneReputation)
            .filter((PhoneReputation.phone_number == normalized) | (PhoneReputation.phone_number == raw_number.strip()))
            .first()
        )

        if reporting_device_id:
            dev_hash = hashlib.sha256(reporting_device_id.encode("utf-8")).hexdigest()[:16]
        else:
            dev_hash = hashlib.sha256(f"anon-{now.timestamp()}-{record.report_count if record else 0}".encode("utf-8")).hexdigest()[:16]

        effective_source = source or ("GOV_DATABASE" if is_authority else "COMMUNITY_REPORT")
        is_auth = is_authority or (effective_source in AUTHORITATIVE_SOURCES)

        if record:
            # Parse existing distinct reporting devices
            try:
                distinct_devices = set(json.loads(record.distinct_reporting_devices or "[]"))
            except Exception:
                distinct_devices = set()

            is_new_device = dev_hash not in distinct_devices
            if is_new_device:
                distinct_devices.add(dev_hash)
                record.report_count += 1
                record.distinct_reporting_devices = json.dumps(list(distinct_devices))

            record.last_reported_at = now
            if fraud_category:
                record.fraud_category = cat
            if notes:
                record.notes = f"{record.notes or ''} | {notes}".strip(" |")

            if is_auth:
                record.is_verified_authority = True
                record.source = effective_source

            # Recalculate risk level based on hardened safety policies
            distinct_count = len(distinct_devices) if distinct_devices else record.report_count
            cls._evaluate_hardened_classification(record, distinct_count)

        else:
            distinct_devices = [dev_hash]
            record = PhoneReputation(
                phone_number=normalized,
                risk_level="CRITICAL" if is_auth else "MEDIUM",
                fraud_category=cat,
                report_count=1,
                confidence_score=0.95 if is_auth else 0.50,
                source=effective_source,
                notes=notes,
                distinct_reporting_devices=json.dumps(distinct_devices),
                is_verified_authority=is_auth,
                classification_reason="Verified by authoritative threat registry." if is_auth else "Single unverified community report.",
                dispute_count=0,
                created_at=now,
                last_reported_at=now,
                last_decay_at=now
            )
            db.add(record)

        db.commit()
        db.refresh(record)
        return record

    @classmethod
    def dispute_number(
        cls,
        db: Session,
        raw_number: str,
        reporting_device_id: Optional[str] = None,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Registers a user false-positive dispute against a phone number reputation entry.
        If dispute volume crosses threshold, safely suspends warnings pending review.
        """
        normalized = cls.normalize_number(raw_number)
        record = (
            db.query(PhoneReputation)
            .filter((PhoneReputation.phone_number == normalized) | (PhoneReputation.phone_number == raw_number.strip()))
            .first()
        )

        if not record:
            return {"success": False, "message": "Phone number not found in reputation registry."}

        record.dispute_count += 1
        record.notes = f"{record.notes or ''} | [DISPUTE] {reason or 'User reported false positive'}".strip(" |")

        # False positive mitigation: downgrade if disputed
        if record.dispute_count >= 2:
            if not record.is_verified_authority:
                record.risk_level = "LOW"
                record.confidence_score = max(0.20, record.confidence_score - 0.35)
                record.classification_reason = f"Classification suppressed due to {record.dispute_count} user false-positive disputes."
            else:
                record.classification_reason = f"Authoritative record noted with {record.dispute_count} user dispute flags."

        db.commit()
        db.refresh(record)

        return {
            "success": True,
            "message": "Dispute registered. Reputation score updated.",
            "phone_number": normalized,
            "current_risk_level": record.risk_level,
            "dispute_count": record.dispute_count
        }

    @staticmethod
    def _evaluate_hardened_classification(record: PhoneReputation, distinct_count: int):
        """
        Mandatory safety rule: Community volume alone can NEVER trigger CRITICAL or auto-blocking.
        Only authoritative threat intelligence or verified law enforcement entries can achieve CRITICAL.
        """
        if record.is_verified_authority:
            record.risk_level = "CRITICAL"
            record.confidence_score = 0.95
            record.classification_reason = "Verified threat confirmed by authoritative telecommunications/law enforcement database."
            return

        # Community-driven classification
        if distinct_count >= 2:
            record.risk_level = "HIGH"
            record.confidence_score = min(0.85, 0.50 + (distinct_count * 0.05))
            record.classification_reason = f"Corroborated by {distinct_count} independent reporting devices. Prominent warning displayed; call not auto-rejected."
        else:
            record.risk_level = "MEDIUM"
            record.confidence_score = 0.50
            record.classification_reason = "Single unverified community report. Prominent warning withheld; caution advised."

    @staticmethod
    def _apply_reputation_decay(record: PhoneReputation, now: datetime):
        """
        Decays stale community reports if no new suspicious activity has been confirmed.
        """
        if record.is_verified_authority or record.last_reported_at is None:
            return  # Authoritative records do not silently decay

        last_rep = record.last_reported_at
        if last_rep.tzinfo is None and now.tzinfo is not None:
            last_rep = last_rep.replace(tzinfo=timezone.utc)
        elif last_rep.tzinfo is not None and now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)

        days_stale = (now - last_rep).days
        if days_stale > 120:
            record.risk_level = "LOW"
            record.confidence_score = 0.20
            record.classification_reason = f"Reputation decayed due to 120+ days without confirmed reports."
        elif days_stale > 60 and record.risk_level == "HIGH":
            record.risk_level = "MEDIUM"
            record.confidence_score = max(0.40, record.confidence_score - 0.25)
            record.classification_reason = f"Severity decayed from HIGH to MEDIUM due to 60+ days without reports."
        record.last_decay_at = now

    @staticmethod
    def _get_recommended_action(risk_level: str, category: Optional[str] = None, is_authority: bool = False) -> str:
        rl = risk_level.upper()
        if rl == "CRITICAL":
            if is_authority:
                return "VERIFIED SCAM THREAT: Authoritatively verified fraud / digital arrest caller. Telephony auto-rejection policy active. Decline call immediately."
            return "HIGH RISK CALLER: Potential scam. Decline call immediately and report to authorities."
        elif rl in {"HIGH"}:
            return "WARNING: Suspicious caller reported by multiple independent users. Proceed with vigilance; never disclose credentials."
        elif rl == "MEDIUM":
            return "CAUTION: Unverified caller with single community report. Verify caller identity."
        elif rl == "SAFE":
            return "VERIFIED: Known legitimate caller or official communication service."
        return "Unverified caller. Never share OTPs, PINs, or transfer money under pressure."


phone_reputation_service = PhoneReputationService()
