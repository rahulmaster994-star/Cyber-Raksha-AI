"""
Cyber Raksha AI - Core Configuration Module
Stage 1: Complete Project Foundation
"""
import os
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True, extra="ignore")

    APP_NAME: str = "Cyber Raksha AI"
    APP_ENV: str = "development"
    APP_VERSION: str = "1.0.0-rc.1"
    STAGE: str = "Stage 1-10: Release Candidate & Production Packaging"
    DEBUG: bool = True
    API_V1_STR: str = "/api/v1"
    ADMIN_SECRET_KEY: str = "cyber-raksha-admin-secret-key-2026"
    
    # SQLite default, designed for seamless PostgreSQL migration in future stages
    DATABASE_URL: str = "sqlite:///./cyber_raksha.db"

    @property
    def normalized_database_url(self) -> str:
        """
        Normalizes database URLs for SQLAlchemy 2.0+ compatibility.
        Converts postgres:// to postgresql:// and handles connection flags.
        """
        url = (self.DATABASE_URL or "").strip()
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql://", 1)
        return url
    
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    
    # Phase A2 Threat Intelligence Automation
    THREAT_INTEL_AUTO_SYNC_ENABLED: bool = True
    THREAT_INTEL_SYNC_INTERVAL_MINUTES: int = 60
    THREAT_INDICATOR_TTL_DAYS: int = 30

    # Phase B2.1 & B3 Cryptographic Secrets
    # Pepper key for HMAC-based SMS threat hashing (immune to rainbow table attacks)
    SMS_PEPPER_KEY: str = os.getenv("CYBER_RAKSHA_SMS_PEPPER", "CYBER_RAKSHA_MOBILE_SMS_PEPPER_V2_1")
    JWT_SECRET_KEY: str = os.getenv("CYBER_RAKSHA_JWT_SECRET", "cyber-raksha-jwt-secret-key-2026-production")
    OTP_EXPIRY_MINUTES: int = 10
    OTP_MAX_ATTEMPTS: int = 3

    # SMTP Configuration for Email Notifications
    SMTP_HOST: str = os.getenv("SMTP_HOST", "")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USERNAME: str = os.getenv("SMTP_USERNAME", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    SMTP_FROM_EMAIL: str = os.getenv("SMTP_FROM_EMAIL", "noreply@cyberraksha.ai")
    SMTP_FROM_NAME: str = os.getenv("SMTP_FROM_NAME", "Cyber Raksha AI")
    SMTP_USE_TLS: bool = os.getenv("SMTP_USE_TLS", "true").lower() in ("true", "1", "yes")

    # Telecom SMS Gateway Configuration for Physical OTP Delivery
    FAST2SMS_API_KEY: str = os.getenv("FAST2SMS_API_KEY", "")
    TWILIO_ACCOUNT_SID: str = os.getenv("TWILIO_ACCOUNT_SID", "")
    TWILIO_AUTH_TOKEN: str = os.getenv("TWILIO_AUTH_TOKEN", "")
    TWILIO_FROM_NUMBER: str = os.getenv("TWILIO_FROM_NUMBER", "")
    
    # CORS Origins (supports both CORS_ORIGINS and ALLOWED_ORIGINS env vars)
    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000,http://127.0.0.1:3000"

    @property
    def cors_origin_list(self) -> List[str]:
        raw = os.getenv("CORS_ORIGINS", os.getenv("ALLOWED_ORIGINS", self.CORS_ORIGINS))
        return [origin.strip() for origin in raw.split(",") if origin.strip()]


settings = Settings()
