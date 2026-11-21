"""
Cyber Raksha AI - Database Engine and Session Management
"""
import time
from typing import Generator
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from app.core.config import settings
from app.database.base import Base

# Configure engine with thread safety for SQLite and connection pooling for PostgreSQL
db_url = settings.normalized_database_url
connect_args = {}
engine_kwargs = {
    "echo": False,
    "pool_pre_ping": True,
}

if db_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False, "timeout": 30.0}
else:
    # PostgreSQL production optimizations (Neon / Supabase / Render)
    engine_kwargs["pool_size"] = 10
    engine_kwargs["max_overflow"] = 20
    engine_kwargs["pool_recycle"] = 300

engine = create_engine(
    db_url,
    connect_args=connect_args,
    **engine_kwargs
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    """
    Initializes database schema. Automatically creates all tables
    registered with the Base metadata and runs safe incremental column migrations for SQLite.
    """
    # Import all models to ensure they are registered with Base metadata
    from app import models  # noqa: F401
    from app.models.user import User
    from app.models.system_config import SystemConfig
    from app.models.security_event import SecurityEvent
    from app.models.analysis_history import AnalysisHistory
    from app.models.notification import Notification, NotificationPreference
    from app.models.threat_intel import ThreatIndicator, ThreatFeedLog, UnifiedRiskRecord
    from app.models.incident import SecurityIncident, IncidentAction, UserProtectionSetting
    from app.models.feedback import AnalysisFeedback
    from app.models.device import Device
    from app.models.phone_reputation import PhoneReputation
    from app.models.sms_analysis import SmsAnalysis
    from app.models.complaint import CybercrimeComplaint
    from app.models.community_report import CommunityReport
    from app.models.keypad_protection import KeypadElderlyUser, KeypadScamReport, KeypadIncident
    from app.models.admin_audit import AdminAuditLog

    Base.metadata.create_all(bind=engine)

    # SQLite non-destructive schema migration for Phase A3 & B2.1 columns
    if engine.dialect.name != "sqlite":
        return

    try:
        with engine.connect() as conn:
            # Users migration
            user_info = conn.execute(text("PRAGMA table_info(users)")).fetchall()
            user_cols = {col[1] for col in user_info}
            if user_cols:
                new_user_cols = [
                    ("mobile_number", "VARCHAR(20)"),
                    ("is_mobile_verified", "BOOLEAN DEFAULT 0"),
                    ("is_email_verified", "BOOLEAN DEFAULT 0"),
                    ("email_verification_token", "VARCHAR(255)"),
                    ("email_token_expires_at", "DATETIME"),
                    ("mobile_otp", "VARCHAR(10)"),
                    ("mobile_otp_expires_at", "DATETIME"),
                    ("mobile_otp_attempts", "INTEGER DEFAULT 0"),
                    ("consent_given", "BOOLEAN DEFAULT 0"),
                    ("consent_timestamp", "DATETIME"),
                ]
                for col_name, col_def in new_user_cols:
                    if col_name not in user_cols:
                        conn.execute(text(f"ALTER TABLE users ADD COLUMN {col_name} {col_def}"))
            # Notifications migration
            table_info = conn.execute(text("PRAGMA table_info(notifications)")).fetchall()
            existing_cols = {col[1] for col in table_info}
            if existing_cols:
                new_columns = [
                    ("device_id", "VARCHAR(100)"),
                    ("severity", "VARCHAR(20) DEFAULT 'INFO'"),
                    ("category", "VARCHAR(50) DEFAULT 'GENERAL'"),
                    ("target_domain", "VARCHAR(255)"),
                    ("recommended_action", "VARCHAR(255)"),
                    ("source_component", "VARCHAR(50) DEFAULT 'SYSTEM'"),
                    ("metadata_json", "TEXT"),
                ]
                for col_name, col_def in new_columns:
                    if col_name not in existing_cols:
                        conn.execute(text(f"ALTER TABLE notifications ADD COLUMN {col_name} {col_def}"))

            # Devices migration (Phase B2.1 authentication)
            device_info = conn.execute(text("PRAGMA table_info(devices)")).fetchall()
            dev_cols = {col[1] for col in device_info}
            if dev_cols:
                if "device_token_hash" not in dev_cols:
                    conn.execute(text("ALTER TABLE devices ADD COLUMN device_token_hash VARCHAR(64)"))
                if "is_revoked" not in dev_cols:
                    conn.execute(text("ALTER TABLE devices ADD COLUMN is_revoked BOOLEAN DEFAULT 0"))

            # Phone Reputations migration (Phase B2.1 hardening)
            rep_info = conn.execute(text("PRAGMA table_info(phone_reputations)")).fetchall()
            rep_cols = {col[1] for col in rep_info}
            if rep_cols:
                if "distinct_reporting_devices" not in rep_cols:
                    conn.execute(text("ALTER TABLE phone_reputations ADD COLUMN distinct_reporting_devices TEXT"))
                if "is_verified_authority" not in rep_cols:
                    conn.execute(text("ALTER TABLE phone_reputations ADD COLUMN is_verified_authority BOOLEAN DEFAULT 0"))
                if "classification_reason" not in rep_cols:
                    conn.execute(text("ALTER TABLE phone_reputations ADD COLUMN classification_reason TEXT"))
                if "dispute_count" not in rep_cols:
                    conn.execute(text("ALTER TABLE phone_reputations ADD COLUMN dispute_count INTEGER DEFAULT 0"))
                if "last_decay_at" not in rep_cols:
                    conn.execute(text("ALTER TABLE phone_reputations ADD COLUMN last_decay_at DATETIME"))

            # Security Events migration (Phase B3 Unified Threat Event Model)
            ev_info = conn.execute(text("PRAGMA table_info(security_events)")).fetchall()
            ev_cols = {col[1] for col in ev_info}
            if ev_cols:
                new_ev_cols = [
                    ("event_id", "VARCHAR(64)"),
                    ("device_id", "VARCHAR(64)"),
                    ("threat_indicator", "VARCHAR(255)"),
                    ("risk_score", "FLOAT DEFAULT 0.0"),
                    ("detection_reason", "TEXT"),
                    ("verification_status", "VARCHAR(50) DEFAULT 'UNVERIFIED'"),
                    ("incident_id", "INTEGER"),
                    ("processing_status", "VARCHAR(50) DEFAULT 'PROCESSED'"),
                    ("event_hash", "VARCHAR(64)")
                ]
                for col_name, col_def in new_ev_cols:
                    if col_name not in ev_cols:
                        conn.execute(text(f"ALTER TABLE security_events ADD COLUMN {col_name} {col_def}"))

            # Security Incidents migration (Phase B3 Central Incident Management)
            inc_info = conn.execute(text("PRAGMA table_info(security_incidents)")).fetchall()
            inc_cols = {col[1] for col in inc_info}
            if inc_cols:
                new_inc_cols = [
                    ("target_or_indicator", "VARCHAR(255)"),
                    ("source_components", "TEXT"),
                    ("device_id", "VARCHAR(64)"),
                    ("user_acknowledged", "BOOLEAN DEFAULT 0"),
                    ("acknowledged_at", "DATETIME"),
                    ("is_false_positive", "BOOLEAN DEFAULT 0")
                ]
                for col_name, col_def in new_inc_cols:
                    if col_name not in inc_cols:
                        conn.execute(text(f"ALTER TABLE security_incidents ADD COLUMN {col_name} {col_def}"))

            # Cybercrime Complaints migration
            cmp_info = conn.execute(text("PRAGMA table_info(cybercrime_complaints)")).fetchall()
            cmp_cols = {col[1] for col in cmp_info}
            if cmp_cols:
                if "verification_level" not in cmp_cols:
                    conn.execute(text("ALTER TABLE cybercrime_complaints ADD COLUMN verification_level VARCHAR(50) DEFAULT 'USER_REPORTED_UNVERIFIED'"))
                if "is_government_verified" not in cmp_cols:
                    conn.execute(text("ALTER TABLE cybercrime_complaints ADD COLUMN is_government_verified BOOLEAN DEFAULT 0"))

            # Community Reports migration
            com_info = conn.execute(text("PRAGMA table_info(community_reports)")).fetchall()
            com_cols = {col[1] for col in com_info}
            if com_cols:
                if "distinct_reporters_count" not in com_cols:
                    conn.execute(text("ALTER TABLE community_reports ADD COLUMN distinct_reporters_count INTEGER DEFAULT 1"))
                if "reporting_identities_json" not in com_cols:
                    conn.execute(text("ALTER TABLE community_reports ADD COLUMN reporting_identities_json TEXT DEFAULT '[]'"))
                if "consensus_score" not in com_cols:
                    conn.execute(text("ALTER TABLE community_reports ADD COLUMN consensus_score FLOAT DEFAULT 0.2"))
                if "is_auto_promoted" not in com_cols:
                    conn.execute(text("ALTER TABLE community_reports ADD COLUMN is_auto_promoted BOOLEAN DEFAULT 0"))

            conn.commit()
    except Exception as e:
        import logging
        logging.getLogger("cyber_raksha.database").warning(f"Schema migration notice: {e}")


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that provides a database session per request
    and handles automatic cleanup.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_db_connection() -> tuple[bool, float, str]:
    """
    Performs an active connectivity test against the database.
    Returns (is_connected, latency_ms, message).
    """
    start_time = time.perf_counter()
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        latency_ms = (time.perf_counter() - start_time) * 1000
        return True, round(latency_ms, 2), "Database connection active and responsive"
    except Exception as e:
        latency_ms = (time.perf_counter() - start_time) * 1000
        return False, round(latency_ms, 2), f"Database connection error: {str(e)}"
