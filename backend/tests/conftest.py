"""
Cyber Raksha AI - Test Configuration and Fixtures
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database.base import Base
from app.database.session import get_db, init_db
from app.models.user import User
from app.models.system_config import SystemConfig
from app.models.security_event import SecurityEvent
from app.models.analysis_history import AnalysisHistory
from app.models.notification import Notification, NotificationPreference
from app.models.device import Device

# Use a persistent test SQLite database file for the test session
TEST_DATABASE_URL = "sqlite:///./test_cyber_raksha.db"

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """Initializes the database schema before tests run."""
    import os
    from sqlalchemy import text
    Base.metadata.create_all(bind=test_engine)
    try:
        with test_engine.connect() as conn:
            table_info = conn.execute(text("PRAGMA table_info(notifications)")).fetchall()
            existing_cols = {col[1] for col in table_info}
            if existing_cols and "device_id" not in existing_cols:
                conn.execute(text("ALTER TABLE notifications ADD COLUMN device_id VARCHAR(100)"))
                conn.commit()
    except Exception:
        pass
    yield
    Base.metadata.drop_all(bind=test_engine)
    test_engine.dispose()
    if os.path.exists("./test_cyber_raksha.db"):
        try:
            os.remove("./test_cyber_raksha.db")
        except Exception:
            pass


@pytest.fixture
def db_session():
    """Provides a transactional database session for tests."""
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db_session):
    """Provides a FastAPI TestClient with database session override."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app, headers={"x-test-bypass-rate-limit": "true"}) as test_client:
        yield test_client
    app.dependency_overrides.clear()
