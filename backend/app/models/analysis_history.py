"""
Cyber Raksha AI - Analysis History Database Model
"""
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, Float, DateTime
from app.database.base import Base


class AnalysisHistory(Base):
    __tablename__ = "analysis_history"

    id = Column(Integer, primary_key=True, index=True)
    module_code = Column(String(50), index=True, nullable=False)  # PHISHING, URL, VOICE, COMM, INTEL, RISK
    target_identifier = Column(String(255), nullable=False)  # Hash, URL, Phone, Domain, or Text snippet
    status = Column(String(50), default="PENDING", nullable=False)  # PENDING, ANALYZING, COMPLETED, FAILED
    risk_score = Column(Float, nullable=True)  # 0.0 to 100.0
    threat_category = Column(String(100), nullable=True)
    summary = Column(Text, nullable=True)
    explanation = Column(Text, nullable=True)
    metadata_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    def __repr__(self) -> str:
        return f"<AnalysisHistory id={self.id} module={self.module_code} status={self.status}>"
