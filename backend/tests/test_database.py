"""
Test Database Models and Session Persistence
"""
from app.models.user import User
from app.models.system_config import SystemConfig
from app.models.security_event import SecurityEvent
from app.models.analysis_history import AnalysisHistory
from app.models.notification import Notification
from app.utils.helpers import hash_password_fallback, verify_password_fallback


def test_user_model_and_password_hashing(db_session):
    raw_password = "SecureStage1Password!"
    hashed = hash_password_fallback(raw_password)
    assert verify_password_fallback(raw_password, hashed) is True
    assert verify_password_fallback("WrongPassword", hashed) is False

    user = User(
        email="analyst@cyberraksha.ai",
        username="lead_analyst",
        hashed_password=hashed,
        full_name="Lead Cyber Security Analyst",
        role="analyst"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    assert user.id is not None
    assert user.email == "analyst@cyberraksha.ai"
    assert user.is_active is True


def test_system_config_model(db_session):
    config = SystemConfig(
        config_key="security_log_level",
        config_value="DEBUG",
        description="Logging level for security alerts"
    )
    db_session.add(config)
    db_session.commit()
    db_session.refresh(config)

    assert config.id is not None
    assert config.config_key == "security_log_level"
    assert config.config_value == "DEBUG"


def test_security_event_model(db_session):
    event = SecurityEvent(
        event_type="SYSTEM_BOOT",
        severity="INFO",
        source_component="FastAPI_Engine",
        description="Cyber Raksha AI stage 1 initialized successfully"
    )
    db_session.add(event)
    db_session.commit()
    db_session.refresh(event)

    assert event.id is not None
    assert event.event_type == "SYSTEM_BOOT"
    assert event.is_resolved is False


def test_analysis_history_model(db_session):
    history = AnalysisHistory(
        module_code="PHISH_DETECT",
        target_identifier="test-sample-id-001",
        status="PENDING",
        summary="Stage 1 architectural placeholder test record"
    )
    db_session.add(history)
    db_session.commit()
    db_session.refresh(history)

    assert history.id is not None
    assert history.module_code == "PHISH_DETECT"
    assert history.status == "PENDING"


def test_notification_model(db_session):
    notif = Notification(
        title="Stage 1 Online",
        message="Cyber Raksha AI project foundation initialized.",
        notification_type="INFO"
    )
    db_session.add(notif)
    db_session.commit()
    db_session.refresh(notif)

    assert notif.id is not None
    assert notif.is_read is False
