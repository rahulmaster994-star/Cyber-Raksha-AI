"""
Cyber Raksha AI - Health Check Schemas
"""
from datetime import datetime
from pydantic import BaseModel, Field


class HealthCheckResponse(BaseModel):
    status: str = Field(..., description="Overall backend health status (healthy/degraded)")
    application: str = Field(..., description="Application name")
    version: str = Field(..., description="Application semantic version")
    stage: str = Field(..., description="Current project development stage")
    database_connected: bool = Field(..., description="Database connectivity indicator")
    database_latency_ms: float = Field(..., description="Database query ping latency in milliseconds")
    database_message: str = Field(..., description="Database connection diagnosis message")
    uptime_seconds: float = Field(..., description="Server uptime in seconds")
    timestamp: datetime = Field(..., description="Timestamp of the health check evaluation")
