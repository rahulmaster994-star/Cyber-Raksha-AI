"""
Cyber Raksha AI - FastAPI Main Application
Stage 8: Final System Integration, Security Hardening & Deployment
"""
import sys
from pathlib import Path

# Defensive path insertion ensuring both backend and root are in sys.path in all environments
_backend_dir = Path(__file__).resolve().parent.parent
_project_root = _backend_dir.parent
for _p in (str(_backend_dir), str(_project_root)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.security import SecurityHeadersMiddleware, RateLimiterMiddleware
from app.core.observability import RequestObservabilityMiddleware
from app.core.feature_flags import feature_flags
from app.database.session import init_db
from app.api.routes.health import router as health_router
from app.api.routes.system import router as system_router
from app.api.routes.modules import router as modules_router
from app.api.routes.detection import router as detection_router
from app.api.routes.communication import router as communication_router
from app.api.routes.audio import router as audio_router
from app.api.routes.threat_intel import router as threat_intel_router
from app.api.routes.prevention import router as prevention_router
from app.api.routes.privacy import router as privacy_router
from app.api.routes.jobs import router as jobs_router
from app.api.routes.monitoring import router as monitoring_router
from app.api.routes.admin import router as admin_router
from app.api.routes.feedback import router as feedback_router
from app.api.routes.notifications import router as notification_router
from app.api.routes.devices import router as device_router
from app.api.routes.mobile import router as mobile_router
from app.api.routes.security import router as security_router
from app.api.routes.dashboard import router as dashboard_router
from app.api.routes.auth import router as auth_router
from app.api.routes.complaints import router as complaints_router
from app.api.routes.community import router as community_router
from app.schemas.system import RootResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan events: initialize database schema on startup, validate production secrets,
    and manage background schedulers.
    """
    # Phase B3.1: Strict Production Secrets Validation
    if not settings.DEBUG or settings.APP_ENV == "production":
        pepper = (settings.SMS_PEPPER_KEY or "").strip()
        if not pepper or pepper == "CYBER_RAKSHA_MOBILE_SMS_PEPPER_V2_1" or len(pepper) < 32:
            raise RuntimeError(
                "CRITICAL SECURITY CONFIGURATION ERROR: CYBER_RAKSHA_SMS_PEPPER must be configured with a non-default secret of at least 32 characters in production."
            )
        admin_key = (settings.ADMIN_SECRET_KEY or "").strip()
        if not admin_key or admin_key == "cyber-raksha-admin-secret-key-2026" or len(admin_key) < 32:
            raise RuntimeError(
                "CRITICAL SECURITY CONFIGURATION ERROR: ADMIN_SECRET_KEY must be configured with a strong non-default secret of at least 32 characters in production."
            )

    init_db()
    # Phase A2: Start Threat Intelligence Scheduler
    try:
        from app.services.threat_intel_scheduler import threat_intel_scheduler
        await threat_intel_scheduler.start()
    except Exception as e:
        import logging
        logging.getLogger("cyber_raksha").error(f"Failed to start threat intel scheduler: {e}")

    yield

    # Shutdown: Stop Threat Intelligence Scheduler
    try:
        from app.services.threat_intel_scheduler import threat_intel_scheduler
        await threat_intel_scheduler.stop()
    except Exception:
        pass


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Cyber Raksha AI: Unified Threat Detection, Prevention & Incident Response Platform",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# 1. Defensive Security Headers Middleware
app.add_middleware(SecurityHeadersMiddleware)

# 2. In-Memory Rate Limiting Middleware (120 req/min general, 30 req/min heavy)
app.add_middleware(RateLimiterMiddleware, general_limit=120, heavy_limit=30, window_seconds=60)

# 3. Stage 9 Observability & Latency Tracking Middleware
app.add_middleware(RequestObservabilityMiddleware)

# 4. Stage 9 Maintenance Mode Guard
@app.middleware("http")
async def maintenance_mode_guard(request: Request, call_next):
    if feature_flags.is_enabled("maintenance_mode"):
        allowed_prefixes = (
            "/api/health", "/api/v1/health", "/health",
            "/api/monitoring", "/api/v1/monitoring",
            "/api/admin", "/api/v1/admin",
            "/docs", "/redoc", "/openapi.json"
        )
        if not any(request.url.path.startswith(p) for p in allowed_prefixes) and request.url.path != "/":
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={
                    "error": "Maintenance Mode",
                    "message": "Cyber Raksha AI is temporarily undergoing scheduled maintenance.",
                    "stage": settings.STAGE
                }
            )
    return await call_next(request)

# 3. CORS Configuration
# When credentials are enabled, origins must be explicit list rather than '*'
cors_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8000",
    "http://127.0.0.1:8000"
]
if not settings.DEBUG:
    cors_origins = settings.cors_origin_list

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_origin_regex=r"^https:\/\/[a-zA-Z0-9\-_.]+\.vercel\.app$",
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Global Exception Handler for safe error responses
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred while processing the request.",
            "path": str(request.url.path),
            "stage": settings.STAGE
        }
    )

# Root Endpoint
@app.get(
    "/",
    response_model=RootResponse,
    status_code=status.HTTP_200_OK,
    summary="Cyber Raksha AI Root Status",
    description="Returns application name, version, development stage, and status."
)
def root() -> RootResponse:
    return RootResponse(
        name=settings.APP_NAME,
        version=settings.APP_VERSION,
        status="OPERATIONAL",
        stage=settings.STAGE,
        docs_url="/docs",
        health_url="/api/health",
        system_info_url="/api/system/info"
    )

# Direct /api routes as required by Stage 1 specification
app.include_router(health_router)
app.include_router(health_router, prefix="/api")
app.include_router(system_router, prefix="/api")
app.include_router(modules_router, prefix="/api")
app.include_router(detection_router, prefix="/api")
app.include_router(communication_router, prefix="/api")
app.include_router(audio_router, prefix="/api")
app.include_router(threat_intel_router, prefix="/api")
app.include_router(prevention_router, prefix="/api")
app.include_router(privacy_router, prefix="/api")
app.include_router(jobs_router, prefix="/api")
app.include_router(monitoring_router, prefix="/api")
app.include_router(feedback_router, prefix="/api")
app.include_router(admin_router, prefix="/api")
app.include_router(notification_router, prefix="/api")
app.include_router(device_router, prefix="/api")
app.include_router(mobile_router, prefix="/api")
app.include_router(security_router, prefix="/api")
app.include_router(dashboard_router, prefix="/api")
app.include_router(auth_router, prefix="/api")
app.include_router(complaints_router, prefix="/api")
app.include_router(community_router, prefix="/api")

# Versioned /api/v1 routes for Stages 2 through 9
app.include_router(health_router, prefix="/api/v1")
app.include_router(system_router, prefix="/api/v1")
app.include_router(modules_router, prefix="/api/v1")
app.include_router(detection_router, prefix="/api/v1")
app.include_router(communication_router, prefix="/api/v1")
app.include_router(audio_router, prefix="/api/v1")
app.include_router(threat_intel_router, prefix="/api/v1")
app.include_router(prevention_router, prefix="/api/v1")
app.include_router(privacy_router, prefix="/api/v1")
app.include_router(jobs_router, prefix="/api/v1")
app.include_router(monitoring_router, prefix="/api/v1")
app.include_router(feedback_router, prefix="/api/v1")
app.include_router(admin_router, prefix="/api/v1")
app.include_router(notification_router, prefix="/api/v1")
app.include_router(device_router, prefix="/api/v1")
app.include_router(mobile_router, prefix="/api/v1")
app.include_router(security_router, prefix="/api/v1")
app.include_router(dashboard_router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1")
app.include_router(complaints_router, prefix="/api/v1")
app.include_router(community_router, prefix="/api/v1")
