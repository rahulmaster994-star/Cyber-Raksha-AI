"""
Cyber Raksha AI - Security Modules Catalog Route
"""
from fastapi import APIRouter, status
from app.schemas.module import SecurityModulesListResponse
from app.services.system_service import system_service

router = APIRouter(prefix="/modules", tags=["Security Modules"])


@router.get(
    "",
    response_model=SecurityModulesListResponse,
    status_code=status.HTTP_200_OK,
    summary="List Security Modules",
    description="Returns the six core Cyber Raksha AI security modules and their planned status (PLANNED / NOT IMPLEMENTED)."
)
def get_security_modules() -> SecurityModulesListResponse:
    return system_service.get_modules()
