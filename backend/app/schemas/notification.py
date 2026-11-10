"""
backend/app/schemas/notification.py
Pydantic Schemas for Phase A3: Intelligent Security Notification & Alert Engine.
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class NotificationCreate(BaseModel):
    device_id: Optional[str] = Field(None, max_length=100, description="Device UUID if device-specific alert")
    title: str = Field(..., min_length=3, max_length=200, description="Brief notification headline")
    message: str = Field(..., min_length=5, max_length=2000, description="Detailed notification message")
    severity: str = Field("LOW", description="CRITICAL, HIGH, MEDIUM, or LOW")
    category: str = Field("SECURITY_ALERT", description="MALICIOUS_WEBSITE, PHISHING_ATTEMPT, HIGH_RISK_URL, THREAT_INTEL_SYNC, SYSTEM_ALERT")
    target_domain: Optional[str] = Field(None, max_length=255, description="Domain or URL of the threat")
    recommended_action: Optional[str] = Field(None, max_length=255, description="Recommended user mitigation")
    source_component: str = Field("BROWSER_EXTENSION", max_length=100, description="Component reporting the notification")
    metadata_json: Optional[Dict[str, Any]] = Field(None, description="Additional structured telemetry")


class NotificationResponse(BaseModel):
    id: int
    device_id: Optional[str] = None
    title: str
    message: str
    notification_type: str
    severity: str
    category: str
    target_domain: Optional[str] = None
    recommended_action: Optional[str] = None
    source_component: str
    metadata_json: Optional[str] = None
    is_read: bool
    recipient_role: str
    created_at: str

    model_config = ConfigDict(from_attributes=True)


class NotificationListResponse(BaseModel):
    total: int
    unread_count: int
    items: List[NotificationResponse]


class NotificationUnreadCountResponse(BaseModel):
    unread_count: int


class NotificationPreferenceResponse(BaseModel):
    user_id: str
    browser_notifications_enabled: bool
    min_severity: str
    categories_enabled: List[str]
    sound_enabled: bool
    updated_at: str

    model_config = ConfigDict(from_attributes=True)


class NotificationPreferenceUpdate(BaseModel):
    browser_notifications_enabled: Optional[bool] = None
    min_severity: Optional[str] = Field(None, description="LOW, MEDIUM, HIGH, CRITICAL")
    categories_enabled: Optional[List[str]] = None
    sound_enabled: Optional[bool] = None

