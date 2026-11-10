from app.api.routes.health import router as health_router
from app.api.routes.system import router as system_router
from app.api.routes.modules import router as modules_router
from app.api.routes.detection import router as detection_router
from app.api.routes.communication import router as communication_router
from app.api.routes.audio import router as audio_router
from app.api.routes.threat_intel import router as threat_intel_router
from app.api.routes.prevention import router as prevention_router

__all__ = [
    "health_router",
    "system_router",
    "modules_router",
    "detection_router",
    "communication_router",
    "audio_router",
    "threat_intel_router",
    "prevention_router"
]
