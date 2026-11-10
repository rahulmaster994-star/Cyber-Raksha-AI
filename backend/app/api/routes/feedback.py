"""
backend/app/api/routes/feedback.py
Stage 9: User Feedback Submission & Human Review Queue.
Accepts user verdicts on threat analysis results for human governance review.
Does NOT trigger automatic model retraining.
"""
from typing import Optional
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.feedback import AnalysisFeedback
from app.core.feature_flags import feature_flags

router = APIRouter(tags=["User Feedback & Review"])

VALID_CATEGORIES = {
    "CORRECT_THREAT",
    "FALSE_POSITIVE",
    "FALSE_NEGATIVE",
    "INCORRECT_CATEGORY",
    "UNSURE",
    "OTHER",
}

VALID_REVIEW_STATUSES = {
    "PENDING",
    "UNDER_REVIEW",
    "CONFIRMED",
    "REJECTED",
    "INCONCLUSIVE",
}


# --- Request/Response Schemas ---

class FeedbackSubmitRequest(BaseModel):
    analysis_id: Optional[int] = Field(
        None, description="ID of the analysis history record (if available)"
    )
    target_identifier: Optional[str] = Field(
        None,
        max_length=255,
        description="URL, message excerpt, or file name that was analyzed",
    )
    feedback_category: str = Field(
        ...,
        description="Feedback type: CORRECT_THREAT | FALSE_POSITIVE | FALSE_NEGATIVE | INCORRECT_CATEGORY | UNSURE | OTHER",
    )
    user_explanation: Optional[str] = Field(
        None,
        max_length=2000,
        description="Optional plain-text explanation from the user",
    )
    user_provided_label: Optional[str] = Field(
        None,
        max_length=100,
        description="Optional label the user believes is correct",
    )

    model_config = {"str_strip_whitespace": True}


class ReviewUpdateRequest(BaseModel):
    review_status: str = Field(
        ...,
        description="New review status: UNDER_REVIEW | CONFIRMED | REJECTED | INCONCLUSIVE",
    )
    reviewer_notes: Optional[str] = Field(None, max_length=2000)
    reviewed_by: Optional[str] = Field(None, max_length=100)

    model_config = {"str_strip_whitespace": True}


# --- Routes ---

@router.post(
    "/feedback/submit",
    status_code=status.HTTP_201_CREATED,
    summary="Submit Analysis Feedback",
    description=(
        "Allows users to report whether a detection was correct, a false positive, "
        "false negative, or other issue. Feedback is queued for human review. "
        "It does NOT automatically change AI models."
    ),
)
def submit_feedback(
    payload: FeedbackSubmitRequest,
    db: Session = Depends(get_db),
):
    if not feature_flags.is_enabled("enable_user_feedback"):
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "error": "Feature Disabled",
                "message": "User feedback submission is currently disabled by an administrator.",
            },
        )

    category = payload.feedback_category.upper()
    if category not in VALID_CATEGORIES:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": "Invalid Feedback Category",
                "detail": f"'{payload.feedback_category}' is not a valid category.",
                "valid_categories": sorted(VALID_CATEGORIES),
            },
        )

    record = AnalysisFeedback(
        analysis_id=payload.analysis_id,
        target_identifier=payload.target_identifier,
        feedback_category=category,
        user_explanation=payload.user_explanation,
        user_provided_label=payload.user_provided_label,
        review_status="PENDING",
        created_at=datetime.now(timezone.utc),
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return {
        "feedback_id": record.id,
        "status": "RECEIVED",
        "review_status": record.review_status,
        "feedback_category": record.feedback_category,
        "message": (
            "Thank you. Your feedback has been recorded and queued for human review. "
            "Feedback does not automatically modify AI models."
        ),
        "created_at": record.created_at.isoformat() if record.created_at else None,
    }


@router.get(
    "/feedback/history",
    status_code=status.HTTP_200_OK,
    summary="List Submitted Feedback",
    description="Returns the most recent feedback submissions (up to 50).",
)
def get_feedback_history(
    limit: int = 20,
    db: Session = Depends(get_db),
):
    limit = max(1, min(limit, 50))
    records = (
        db.query(AnalysisFeedback)
        .order_by(AnalysisFeedback.created_at.desc())
        .limit(limit)
        .all()
    )
    return {
        "total": len(records),
        "feedback": [
            {
                "feedback_id": r.id,
                "analysis_id": r.analysis_id,
                "target_identifier": r.target_identifier,
                "feedback_category": r.feedback_category,
                "user_explanation": r.user_explanation,
                "review_status": r.review_status,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in records
        ],
    }

