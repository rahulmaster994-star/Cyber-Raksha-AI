"""
backend/app/models/feedback.py
Stage 9: User Feedback and Human Review Queue Model.
Tracks user feedback on threat analysis results and maintains human reviewer audit records.
"""
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime
from app.database.base import Base


class AnalysisFeedback(Base):
    """
    Stores optional user feedback on detection verdicts.
    Categories:
      - CORRECT_THREAT
      - FALSE_POSITIVE
      - FALSE_NEGATIVE
      - INCORRECT_CATEGORY
      - UNSURE
      - OTHER
    Review Statuses:
      - PENDING
      - UNDER_REVIEW
      - CONFIRMED
      - REJECTED
      - INCONCLUSIVE
    """
    __tablename__ = "analysis_feedback"

    id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(Integer, nullable=True, index=True)
    target_identifier = Column(String(255), nullable=True)
    feedback_category = Column(String(50), nullable=False, index=True)
    user_explanation = Column(Text, nullable=True)
    user_provided_label = Column(String(100), nullable=True)
    review_status = Column(String(50), default="PENDING", nullable=False, index=True)
    reviewer_notes = Column(Text, nullable=True)
    reviewed_by = Column(String(100), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    def __repr__(self) -> str:
        return f"<AnalysisFeedback id={self.id} category={self.feedback_category} status={self.review_status}>"

