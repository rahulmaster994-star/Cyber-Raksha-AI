"""
Cyber Raksha AI - Security Module Schemas
"""
from typing import List
from pydantic import BaseModel, Field


class SecurityModuleInfo(BaseModel):
    id: str = Field(..., description="Unique module identifier")
    name: str = Field(..., description="Human-readable module name")
    code: str = Field(..., description="Short programmatic module code")
    category: str = Field(..., description="Security category")
    status: str = Field("PLANNED", description="Implementation status (PLANNED / NOT IMPLEMENTED)")
    is_implemented: bool = Field(False, description="Flag indicating if real AI model inference is implemented")
    description: str = Field(..., description="Module purpose and architectural role")
    planned_capabilities: List[str] = Field(..., description="List of future AI capabilities")
    stage_planned: str = Field("Stage 2+", description="Target development stage for functional delivery")


class SecurityModulesListResponse(BaseModel):
    total_modules: int
    implemented_count: int
    planned_count: int
    modules: List[SecurityModuleInfo]
