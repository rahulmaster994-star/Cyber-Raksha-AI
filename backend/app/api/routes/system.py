"""
Cyber Raksha AI - System Information Route
"""
from fastapi import APIRouter, status, Depends
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.schemas.system import SystemInfoResponse
from app.services.system_service import system_service

router = APIRouter(prefix="/system", tags=["System Information"])


@router.get(
    "/info",
    response_model=SystemInfoResponse,
    status_code=status.HTTP_200_OK,
    summary="Get System Information and Architecture State",
    description="Returns detailed metadata including application name, version, development stage, implemented components, planned components, and database engine dialect."
)
def get_system_info() -> SystemInfoResponse:
    return system_service.get_system_info()


@router.get(
    "/dashboard-stats",
    status_code=status.HTTP_200_OK,
    summary="Get Live Dashboard Statistics",
    description="Returns genuine real-time statistics aggregated directly from the database for the Central Operations Dashboard."
)
def get_dashboard_stats(db: Session = Depends(get_db)):
    return system_service.get_dashboard_stats(db)
