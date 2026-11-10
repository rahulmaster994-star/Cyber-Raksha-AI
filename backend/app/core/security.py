"""
backend/app/core/security.py
Security middleware, rate limiting, and input sanitization for Cyber Raksha AI.
Stage 8: Security Hardening & Integration
"""
import ipaddress
import time
import re
from typing import Dict, Tuple, Optional, Any
from urllib.parse import urlparse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
from fastapi import HTTPException, status


# Private / loopback / link-local IP ranges that must never be targeted.
_SSRF_BLOCKED_NETS = [
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("169.254.0.0/16"),  # link-local / AWS metadata
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
    ipaddress.ip_network("fe80::/10"),
]


def _is_ssrf_host(hostname: str) -> bool:
    """Return True if the hostname is a loopback, private, or link-local address."""
    lower_host = hostname.lower().rstrip(".")
    # Named loopback
    if lower_host in ("localhost", "localhost.localdomain"):
        return True
    # Numeric IP check
    try:
        addr = ipaddress.ip_address(lower_host)
        return any(addr in net for net in _SSRF_BLOCKED_NETS)
    except ValueError:
        pass
    return False


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Applies defensive HTTP security headers to all outbound responses.
    Mitigates Clickjacking, MIME-sniffing, XSS, and unauthorized framing.
    """
    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"

        # Content-Security-Policy (CSP Level 3) Hardening:
        # Strictly enforces 'self' on script-src across all application and API routes.
        # Eliminates 'unsafe-inline' script execution completely for defense-in-depth against XSS.
        # style-src-attr permits inline style attributes required by React dynamic layout components.
        # Developer documentation (/docs, /redoc) explicitly permits Swagger CDN assets.
        path = request.url.path
        if path.startswith(("/docs", "/redoc")):
            csp = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
                "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
                "style-src-attr 'unsafe-inline'; "
                "style-src-elem 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
                "img-src 'self' data: https: https://fastapi.tiangolo.com; "
                "frame-ancestors 'none'; "
                "base-uri 'self'; "
                "form-action 'self';"
            )
        else:
            csp = (
                "default-src 'self'; "
                "script-src 'self'; "
                "style-src 'self' 'unsafe-inline'; "
                "style-src-attr 'unsafe-inline'; "
                "style-src-elem 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "connect-src 'self' http://127.0.0.1:* http://localhost:* ws://127.0.0.1:* ws://localhost:*; "
                "frame-ancestors 'none'; "
                "base-uri 'self'; "
                "form-action 'self';"
            )
        response.headers["Content-Security-Policy"] = csp
        return response


class RateLimiterMiddleware(BaseHTTPMiddleware):
    """
    In-memory IP-based sliding window rate limiter.
    Protects against brute force and denial of service.
    Default: 120 requests/minute per client IP.
    Heavy endpoints (audio analysis): 30 requests/minute.
    Exempts health probes and OpenAPI documentation.
    """
    def __init__(self, app, general_limit: int = 120, heavy_limit: int = 30, window_seconds: int = 60):
        super().__init__(app)
        self.general_limit = general_limit
        self.heavy_limit = heavy_limit
        self.window_seconds = window_seconds
        # client_ip -> list of timestamps
        self.clients: Dict[str, list[float]] = {}
        self.heavy_clients: Dict[str, list[float]] = {}
        self.exempt_paths = {"/api/health", "/health", "/docs", "/openapi.json", "/redoc", "/"}

    def _get_client_ip(self, request: Request) -> str:
        # SEC-002 FIX: Do NOT trust X-Forwarded-For from arbitrary clients.
        # Only use the real peer connection IP to prevent rate-limit bypass via header spoofing.
        return request.client.host if request.client else "127.0.0.1"

    async def dispatch(self, request: Request, call_next) -> Response:
        path = request.url.path

        # Exempt health probes and API docs.
        # SEC-001 FIX & Phase B3.1 Hardening:
        # Test bypass header is STRICTLY gated by DEBUG mode AND non-production environment.
        # It is strictly impossible to bypass rate limits via request headers in production.
        from app.core.config import settings as _settings  # local import avoids circular
        bypass_allowed = (
            _settings.DEBUG
            and _settings.APP_ENV != "production"
            and request.headers.get("x-test-bypass-rate-limit") == "true"
        )
        if (
            path in self.exempt_paths
            or path.endswith(("/health", "/docs", "/openapi.json"))
            or bypass_allowed
        ):
            return await call_next(request)

        now = time.time()
        client_ip = self._get_client_ip(request)

        # SEC-004 FIX: Prune stale entries if the dict grows too large to prevent
        # memory exhaustion from unbounded unique-IP accumulation.
        if len(self.clients) > 5000:
            self.clients = {
                ip: [ts for ts in tss if now - ts < self.window_seconds]
                for ip, tss in self.clients.items()
            }
            self.clients = {ip: tss for ip, tss in self.clients.items() if tss}
        if len(self.heavy_clients) > 1000:
            self.heavy_clients = {
                ip: [ts for ts in tss if now - ts < self.window_seconds]
                for ip, tss in self.heavy_clients.items()
            }
            self.heavy_clients = {ip: tss for ip, tss in self.heavy_clients.items() if tss}

        # Check heavy endpoint rate limit (e.g. audio upload)
        is_heavy = "/audio/analyze" in path or "/intel/feed/update" in path
        if is_heavy:
            timestamps = self.heavy_clients.get(client_ip, [])
            valid_ts = [ts for ts in timestamps if now - ts < self.window_seconds]
            if len(valid_ts) >= self.heavy_limit:
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "error": "Rate Limit Exceeded",
                        "message": f"Resource-intensive endpoint limit reached ({self.heavy_limit} req/{self.window_seconds}s). Please wait before retrying.",
                        "retry_after_seconds": self.window_seconds
                    },
                    headers={"Retry-After": str(self.window_seconds)}
                )
            valid_ts.append(now)
            self.heavy_clients[client_ip] = valid_ts

        # General rate limit
        timestamps = self.clients.get(client_ip, [])
        valid_ts = [ts for ts in timestamps if now - ts < self.window_seconds]
        if len(valid_ts) >= self.general_limit:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "Rate Limit Exceeded",
                    "message": f"API request limit exceeded ({self.general_limit} req/{self.window_seconds}s). Please wait before retrying.",
                    "retry_after_seconds": self.window_seconds
                },
                headers={"Retry-After": str(self.window_seconds)}
            )
        valid_ts.append(now)
        self.clients[client_ip] = valid_ts

        return await call_next(request)


def validate_safe_url(url: str) -> str:
    """
    Validates URL scheme, structure, and guards against SSRF / local protocol abuse.
    Strictly permits only http and https.
    Rejects file://, javascript:, data:, gopher:, and loopback probing.
    """
    if not url or not url.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="URL parameter cannot be empty."
        )

    clean_url = url.strip()

    # Reject dangerous protocols
    lower = clean_url.lower()
    if lower.startswith(("javascript:", "data:", "file:", "gopher:", "ftp:", "about:", "chrome:")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported or dangerous URL protocol. Only http:// and https:// URLs are permitted."
        )

    try:
        parsed = urlparse(clean_url)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Malformed URL structure."
        )

    if parsed.scheme and parsed.scheme.lower() not in ("http", "https"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Protocol '{parsed.scheme}' is prohibited. Only HTTP and HTTPS are permitted."
        )

    # SEC-007 FIX: Block SSRF probing of loopback, private, and link-local hosts.
    hostname = parsed.hostname or ""
    if _is_ssrf_host(hostname):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="URL targets a private or loopback address, which is not permitted."
        )

    if len(clean_url) > 2048:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="URL exceeds maximum allowable length of 2048 characters."
        )

    return clean_url


# ==============================================================================
# Phase B3.1: Security Context, Caller Identity & Multi-Device Isolation
# ==============================================================================

class SecurityContext:
    """
    Encapsulates authenticated caller identity and authorization scope.
    Distinguishes ADMIN, DEVICE (per-device scoped), and ANONYMOUS callers.
    """
    def __init__(
        self,
        auth_type: str,
        is_authenticated: bool,
        is_admin: bool,
        device_id: Optional[str] = None,
        device: Optional[Any] = None
    ):
        self.auth_type = auth_type          # "ADMIN", "DEVICE", "ANONYMOUS"
        self.is_authenticated = is_authenticated
        self.is_admin = is_admin
        self.device_id = device_id
        self.device = device

    def can_access_device(self, target_device_id: str) -> bool:
        """True if caller is admin or is the exact authenticated device."""
        if self.is_admin:
            return True
        if self.is_authenticated and self.device_id == target_device_id:
            return True
        return False

    def can_access_incident(self, incident: Any) -> bool:
        """
        True if caller is admin, or if incident is global (device_id is None),
        or if caller is the exact device owner of this private incident.
        """
        if self.is_admin:
            return True
        target_dev = getattr(incident, "device_id", None)
        if not target_dev:
            # Global / system-wide incident
            return True
        return self.is_authenticated and self.device_id == target_dev


def get_security_context(request: Request) -> SecurityContext:
    """
    FastAPI dependency that extracts and cryptographically verifies
    caller identity from X-Admin-Key, X-Device-Token, or Authorization Bearer header.
    Guarantees strict multi-device isolation.
    """
    from app.core.config import settings
    from app.database.session import SessionLocal
    from app.models.device import Device
    import hashlib
    import hmac

    # 1. Admin Authentication Check
    admin_key = request.headers.get("X-Admin-Key")
    if admin_key:
        if hmac.compare_digest(admin_key.strip(), settings.ADMIN_SECRET_KEY):
            return SecurityContext(
                auth_type="ADMIN",
                is_authenticated=True,
                is_admin=True,
                device_id=None
            )

    # 2. Check for Single-Use SSE Ticket (Objective 2: Safe SSE Connection Ticket)
    ticket = request.query_params.get("ticket")
    if ticket:
        from app.services.ticket_service import ticket_service
        ticket_data = ticket_service.consume_ticket(ticket)
        if not ticket_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid, expired, or already used SSE connection ticket."
            )
        # Check if the ticket belonged to a revoked device
        if ticket_data.auth_type == "DEVICE" and ticket_data.device_id:
            from app.database.session import SessionLocal
            from app.models.device import Device
            db = SessionLocal()
            try:
                device = db.query(Device).filter(Device.device_id == ticket_data.device_id).first()
                if not device or device.is_revoked or device.status == "REVOKED":
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Device authentication credentials have been revoked."
                    )
            finally:
                db.close()

        return SecurityContext(
            auth_type=ticket_data.auth_type,
            is_authenticated=True,
            is_admin=ticket_data.is_admin,
            device_id=ticket_data.device_id,
            device=None
        )

    # Reject long-lived tokens in query parameters (defense-in-depth against credential leakage in URLs/logs)
    if request.query_params.get("token"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Passing long-lived authentication tokens in URL query parameters is prohibited. Request a single-use SSE ticket via POST /security/stream-ticket."
        )

    # 3. Extract Device Token from Standard Secure Headers
    token = request.headers.get("X-Device-Token")
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:].strip()

    if not token:
        return SecurityContext(
            auth_type="ANONYMOUS",
            is_authenticated=False,
            is_admin=False,
            device_id=None
        )

    # 3. Cryptographic Token Lookup & Validation
    token_hash = hashlib.sha256(token.strip().encode("utf-8")).hexdigest()
    db = SessionLocal()
    try:
        device = db.query(Device).filter(Device.device_token_hash == token_hash).first()
        if not device:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid device authentication credential."
            )
        if device.is_revoked or device.status == "REVOKED":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Device authentication credentials have been revoked."
            )

        return SecurityContext(
            auth_type="DEVICE",
            is_authenticated=True,
            is_admin=False,
            device_id=device.device_id,
            device=device
        )
    finally:
        db.close()

