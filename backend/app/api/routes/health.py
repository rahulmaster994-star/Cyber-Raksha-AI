"""
Cyber Raksha AI - Health Check Route
"""
from fastapi import APIRouter, status
from app.schemas.health import HealthCheckResponse
from app.services.system_service import system_service

router = APIRouter(prefix="/health", tags=["Health & Diagnostics"])


@router.get(
    "",
    response_model=HealthCheckResponse,
    status_code=status.HTTP_200_OK,
    summary="Check Backend and Database Health",
    description="Actively verifies backend availability, computes uptime, and executes a real database query ping to evaluate database connectivity and latency."
)
def get_health() -> HealthCheckResponse:
    return system_service.get_health()
