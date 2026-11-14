"""
Cyber Raksha AI - Community Threat Intelligence & Crowdsourced Reporting Routes
Enables citizens to flag fraudulent phone numbers, UPI handles, phishing domains, and SMS senders.
Includes Sybil defense, duplicate suppression, and abuse-resistant threat classification.
"""
import hashlib
import json
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.community_report import CommunityReport
from app.models.threat_intel import ThreatIndicator
from app.schemas.community import (
    CommunityReportRequest,
    CommunityReportResponse,
    IndicatorReputationResponse
)
from app.api.routes.auth import get_optional_current_user

router = APIRouter(prefix="/community", tags=["Community Threat Intelligence"])


def _extract_reporter_identity(user, req: CommunityReportRequest, request: Request) -> str:
    """Generates an abuse-resistant identity hash for the reporting citizen/device."""
    if user:
        return f"usr_{user.id}"
    if req.device_id and req.device_id.strip():
        return f"dev_{req.device_id.strip()}"
    client_ip = request.client.host if request.client else "127.0.0.1"
    return f"ip_{hashlib.sha256(client_ip.encode('utf-8')).hexdigest()[:12]}"


@router.post("/report", response_model=CommunityReportResponse, status_code=status.HTTP_201_CREATED)
def submit_community_report(
    req: CommunityReportRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Submits a crowdsourced fraud report with Sybil protection.
    Rejects duplicate reports from the same identity to prevent manipulation.
    """
    clean_indicator = req.indicator.strip()
    user = get_optional_current_user(request, db)
    now = datetime.now(timezone.utc)
    reporter_id = _extract_reporter_identity(user, req, request)

    report = db.query(CommunityReport).filter(CommunityReport.indicator == clean_indicator).first()

    if report:
        try:
            identities = json.loads(report.reporting_identities_json or "[]")
        except Exception:
            identities = []

        # Sybil defense: reject duplicate submission from same reporter identity
        if reporter_id in identities:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Duplicate submission rejected. This identity has already filed a report for indicator '{clean_indicator}'."
            )

        identities.append(reporter_id)
        report.reporting_identities_json = json.dumps(identities)
        report.report_count += 1
        report.distinct_reporters_count = len(identities)
        report.updated_at = now
        report.consensus_score = min(0.95, float(report.distinct_reporters_count) * 0.18)

        if req.description:
            report.description = (report.description or "") + f"\n[{now.strftime('%Y-%m-%d')}] {req.description}"

        # Abuse prevention: do NOT auto-promote solely on 3 unverified reports.
        # Only promote if at least 5 distinct reporters consensus is met AND not already promoted.
        if report.distinct_reporters_count >= 5 and not getattr(report, "is_auto_promoted", False):
            existing_indicator = db.query(ThreatIndicator).filter(ThreatIndicator.indicator_value == clean_indicator).first()
            if not existing_indicator:
                new_ind = ThreatIndicator(
                    indicator_type=req.indicator_type.upper(),
                    indicator_value=clean_indicator,
                    threat_type=req.category.upper(),
                    severity="MEDIUM",
                    confidence_score=0.75,
                    source_name="COMMUNITY_CONSENSUS",
                    description=f"Flagged by {report.distinct_reporters_count} distinct Cyber Raksha community users. Pending formal analyst review.",
                    is_active=True
                )
                db.add(new_ind)
                report.is_auto_promoted = True

        db.commit()
        db.refresh(report)
    else:
        identities = [reporter_id]
        report = CommunityReport(
            indicator=clean_indicator,
            indicator_type=req.indicator_type.upper(),
            category=req.category.upper(),
            description=req.description,
            reporter_user_id=user.id if user else None,
            reporter_device_id=req.device_id,
            report_count=1,
            distinct_reporters_count=1,
            reporting_identities_json=json.dumps(identities),
            consensus_score=0.20,
            is_auto_promoted=False,
            severity=req.severity.upper(),
            verified_status="PENDING_REVIEW",
            created_at=now,
            updated_at=now
        )
        db.add(report)
        db.commit()
        db.refresh(report)

    return CommunityReportResponse(
        indicator=report.indicator,
        indicator_type=report.indicator_type,
        category=report.category,
        total_reports=report.report_count,
        severity=report.severity,
        verified_status=report.verified_status,
        status="RECORDED",
        message=f"Threat indicator successfully recorded. Distinct community reports: {report.distinct_reporters_count}."
    )


@router.get("/reputation/{indicator:path}", response_model=IndicatorReputationResponse)
def get_indicator_reputation(
    indicator: str,
    db: Session = Depends(get_db)
):
    """
    Queries community threat reputation and verified status for any indicator.
    Strictly distinguishes unverified community flags from verified malicious indicators.
    """
    clean_ind = indicator.strip()
    report = db.query(CommunityReport).filter(CommunityReport.indicator == clean_ind).first()
    threat_intel = db.query(ThreatIndicator).filter(ThreatIndicator.indicator_value == clean_ind).first()

    total_reports = report.report_count if report else 0
    distinct_reporters = report.distinct_reporters_count if report else 0

    # Never claim confirmed malicious without verified analyst status or verified threat feed
    is_malicious = (threat_intel is not None and threat_intel.confidence_score >= 0.8) or (
        report is not None and report.verified_status == "VERIFIED_MALICIOUS"
    )

    risk_score = 0.0
    if threat_intel:
        risk_score = max(risk_score, threat_intel.confidence_score * 100)
    if distinct_reporters > 0:
        # Score scaled by distinct reporters, capped at 70 for unverified community reports
        community_risk = min(70.0, float(distinct_reporters * 15))
        risk_score = max(risk_score, community_risk)

    top_categories = []
    if report:
        top_categories.append(report.category)
    if threat_intel and threat_intel.threat_type not in top_categories:
        top_categories.append(threat_intel.threat_type.upper())

    ind_type = report.indicator_type if report else (threat_intel.indicator_type.upper() if threat_intel else "UNKNOWN")

    status_str = "SAFE"
    if is_malicious:
        status_str = "CONFIRMED_MALICIOUS"
    elif distinct_reporters >= 5:
        status_str = "HIGH_COMMUNITY_CONSENSUS"
    elif distinct_reporters >= 2:
        status_str = "SUSPICIOUS"
    elif total_reports > 0:
        status_str = "COMMUNITY_REPORTED"

    return IndicatorReputationResponse(
        indicator=clean_ind,
        indicator_type=ind_type,
        is_malicious=is_malicious,
        risk_score=risk_score,
        total_reports=total_reports,
        top_categories=top_categories,
        reputation_status=status_str
    )
