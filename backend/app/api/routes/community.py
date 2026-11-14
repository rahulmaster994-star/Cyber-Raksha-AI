"""
Cyber Raksha AI - Community Threat Intelligence & Crowdsourced Reporting Routes
Enables citizens to flag fraudulent phone numbers, UPI handles, phishing domains, and SMS senders.
"""
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


@router.post("/report", response_model=CommunityReportResponse, status_code=status.HTTP_201_CREATED)
def submit_community_report(
    req: CommunityReportRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """Submits a crowdsourced fraud report for a phone number, URL, UPI ID, or sender."""
    clean_indicator = req.indicator.strip()
    user = get_optional_current_user(request, db)
    now = datetime.now(timezone.utc)

    # Check if indicator already has community reports
    report = db.query(CommunityReport).filter(CommunityReport.indicator == clean_indicator).first()
    if report:
        report.report_count += 1
        report.updated_at = now
        if req.description:
            report.description = (report.description or "") + f"\n[{now.strftime('%Y-%m-%d')}] {req.description}"
        db.commit()
        db.refresh(report)
    else:
        report = CommunityReport(
            indicator=clean_indicator,
            indicator_type=req.indicator_type.upper(),
            category=req.category.upper(),
            description=req.description,
            reporter_user_id=user.id if user else None,
            reporter_device_id=req.device_id,
            report_count=1,
            severity=req.severity.upper(),
            verified_status="PENDING_REVIEW",
            created_at=now,
            updated_at=now
        )
        db.add(report)
        db.commit()
        db.refresh(report)

    # If reported 3 or more times, auto-add to local ThreatIndicator feed
    if report.report_count >= 3:
        existing_indicator = db.query(ThreatIndicator).filter(ThreatIndicator.indicator_value == clean_indicator).first()
        if not existing_indicator:
            new_ind = ThreatIndicator(
                indicator_type=req.indicator_type.upper(),
                indicator_value=clean_indicator,
                threat_type=req.category.upper(),
                severity=req.severity.upper(),
                confidence_score=0.85,
                source_name="COMMUNITY_REPORTS",
                description=f"Flagged by {report.report_count} Cyber Raksha community users.",
                is_active=True
            )
            db.add(new_ind)
            db.commit()

    return CommunityReportResponse(
        indicator=report.indicator,
        indicator_type=report.indicator_type,
        category=report.category,
        total_reports=report.report_count,
        severity=report.severity,
        verified_status=report.verified_status,
        status="RECORDED",
        message=f"Threat indicator successfully reported. Total community reports: {report.report_count}."
    )


@router.get("/reputation/{indicator:path}", response_model=IndicatorReputationResponse)
def get_indicator_reputation(
    indicator: str,
    db: Session = Depends(get_db)
):
    """Queries community threat reputation and verified status for any indicator."""
    clean_ind = indicator.strip()
    report = db.query(CommunityReport).filter(CommunityReport.indicator == clean_ind).first()
    threat_intel = db.query(ThreatIndicator).filter(ThreatIndicator.indicator_value == clean_ind).first()

    total_reports = report.report_count if report else 0
    is_malicious = (threat_intel is not None) or (total_reports >= 3)
    risk_score = 0.0
    if threat_intel:
        risk_score = max(risk_score, threat_intel.confidence_score * 100)
    if total_reports > 0:
        risk_score = min(100.0, max(risk_score, float(total_reports * 25)))

    top_categories = []
    if report:
        top_categories.append(report.category)
    if threat_intel and threat_intel.threat_type not in top_categories:
        top_categories.append(threat_intel.threat_type.upper())

    ind_type = report.indicator_type if report else (threat_intel.indicator_type.upper() if threat_intel else "UNKNOWN")

    status_str = "SAFE"
    if risk_score >= 80:
        status_str = "CONFIRMED_MALICIOUS"
    elif risk_score >= 50:
        status_str = "SUSPICIOUS"
    elif total_reports > 0:
        status_str = "REPORTED"

    return IndicatorReputationResponse(
        indicator=clean_ind,
        indicator_type=ind_type,
        is_malicious=is_malicious,
        risk_score=risk_score,
        total_reports=total_reports,
        top_categories=top_categories,
        reputation_status=status_str
    )
