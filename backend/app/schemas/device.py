"""
Cyber Raksha AI - Device Registration & Status Schemas
Phase B1: Native Android Foundation
"""
import re
from datetime import datetime
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field, field_validator


# Reject 14-16 digit IMEIs and phone number formats
IMEI_PATTERN = re.compile(r"^\d{14,16}$")
PHONE_PATTERN = re.compile(r"^(\+\d{1,3}[- ]?)?\(?\d{3}\)?[- ]?\d{3}[- ]?\d{4}$")
VALID_DEVICE_ID_PATTERN = re.compile(r"^[0-9a-fA-F\-]{16,64}$")


class DeviceRegisterRequest(BaseModel):
    device_id: str = Field(
        ...,
        min_length=16,
        max_length=64,
        description="Application-generated UUID or secure installation identifier."
    )
    device_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Friendly device brand/model (e.g. 'Google Pixel 8 - Android 14')."
    )
    app_version: str = Field(
        default="1.0.0",
        min_length=1,
        max_length=20,
        description="Installed Cyber Raksha AI Android version."
    )

    @field_validator("device_id")
    @classmethod
    def validate_secure_device_id(cls, v: str) -> str:
        clean = v.strip()
        if IMEI_PATTERN.match(clean):
            raise ValueError("Prohibited hardware identifier: IMEI cannot be used as device identity.")
        if PHONE_PATTERN.match(clean):
            raise ValueError("Prohibited personal identifier: Phone number cannot be used as device identity.")
        if not VALID_DEVICE_ID_PATTERN.match(clean):
            raise ValueError("Invalid device_id format. Must be a 16-64 character UUID or secure installation token.")
        return clean

    @field_validator("device_name")
    @classmethod
    def sanitize_device_name(cls, v: str) -> str:
        clean = v.strip()
        if not clean:
            raise ValueError("device_name cannot be blank.")
        return clean


class ProtectionModulesStatus(BaseModel):
    browser_protection: str = Field(default="ACTIVE", description="ACTIVE | INACTIVE | NOT_CONFIGURED")
    threat_intelligence: str = Field(default="ACTIVE", description="ACTIVE | INACTIVE | NOT_CONFIGURED")
    security_notifications: str = Field(default="ACTIVE", description="ACTIVE | INACTIVE | NOT_CONFIGURED")
    mobile_protection: str = Field(default="ACTIVE", description="ACTIVE | INACTIVE | NOT_CONFIGURED")
    sms_protection: str = Field(default="ACTIVE", description="ACTIVE | INACTIVE | NOT_CONFIGURED")
    call_protection: str = Field(default="ACTIVE", description="ACTIVE | INACTIVE | NOT_CONFIGURED")


class DeviceRegistrationResponse(BaseModel):
    device_id: str
    device_name: str
    app_version: str
    status: str = Field(default="ACTIVE")
    security_posture: str = Field(default="PROTECTED")
    device_token: Optional[str] = Field(None, description="Cryptographic device authentication credential.")
    registered_at: datetime
    last_seen_at: datetime
    modules: ProtectionModulesStatus
    server_timestamp: datetime
    message: str = "Device registered and synchronized successfully."


class DeviceStatusResponse(BaseModel):
    device_id: str
    device_name: str
    app_version: str
    status: str
    security_posture: str
    registered_at: datetime
    last_seen_at: datetime
    modules: ProtectionModulesStatus
    server_timestamp: datetime


class DeviceActivityItem(BaseModel):
    id: int
    event_type: str
    severity: str
    description: str
    source_component: str
    created_at: datetime


class DeviceActivityListResponse(BaseModel):
    device_id: str
    total_events: int
    events: List[DeviceActivityItem]
