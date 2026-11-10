"""
Cyber Raksha AI - System Information Schemas
"""
from datetime import datetime
from typing import List, Dict, Any
from pydantic import BaseModel, Field


class SystemInfoResponse(BaseModel):
    application_name: str = Field(..., description="Application name")
    version: str = Field(..., description="Application version")
    development_stage: str = Field(..., description="Current development stage")
    environment: str = Field(..., description="Current running environment")
    backend_status: str = Field(..., description="Backend operational status")
    database_status: Dict[str, Any] = Field(..., description="Database connection and dialect details")
    ai_engine_status: Dict[str, Any] = Field(..., description="AI Engine architecture status")
    implemented_components: List[str] = Field(..., description="List of components implemented in Stage 1")
    planned_components: List[str] = Field(..., description="List of components planned for future stages")
    system_architecture: Dict[str, Any] = Field(..., description="Architectural specifications")
    timestamp: datetime = Field(..., description="Response generation timestamp")


class RootResponse(BaseModel):
    name: str
    version: str
    status: str
    stage: str
    docs_url: str
    health_url: str
    system_info_url: str
