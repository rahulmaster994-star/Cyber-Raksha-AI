"""
Cyber Raksha AI - Single-Use SSE Connection Ticket Service
Phase B3.1 Security Closure: Objective 2

Provides cryptographically random, short-lived, single-use connection tickets
for browser EventSource (SSE) connections. Eliminates the dangerous anti-pattern
of passing long-lived authentication tokens in URL query parameters.
"""
import secrets
import time
import threading
from typing import Optional, Dict, NamedTuple
import logging

logger = logging.getLogger("cyber_raksha.ticket_service")

TICKET_TTL_SECONDS = 60  # Short expiration window


class TicketData(NamedTuple):
    device_id: Optional[str]
    is_admin: bool
    auth_type: str
    created_at: float
    expires_at: float


class TicketService:
    """
    In-memory, thread-safe, single-use connection ticket manager.
    Tickets are one-time-use tokens with short TTL (60s).
    """

    def __init__(self):
        self._tickets: Dict[str, TicketData] = {}
        self._lock = threading.Lock()

    def create_ticket(
        self,
        device_id: Optional[str] = None,
        is_admin: bool = False,
        auth_type: str = "DEVICE",
        ttl_seconds: int = TICKET_TTL_SECONDS
    ) -> str:
        """
        Creates a cryptographically secure, single-use SSE connection ticket.
        Never logs or exposes the ticket secret.
        """
        now = time.time()
        # 32 bytes of cryptographic randomness = 43 base64 characters
        ticket = secrets.token_urlsafe(32)
        ticket_data = TicketData(
            device_id=device_id,
            is_admin=is_admin,
            auth_type=auth_type,
            created_at=now,
            expires_at=now + ttl_seconds
        )

        with self._lock:
            self._purge_expired_locked(now)
            self._tickets[ticket] = ticket_data

        logger.debug("Issued single-use SSE ticket for scope auth_type=%s, is_admin=%s", auth_type, is_admin)
        return ticket

    def consume_ticket(self, ticket: Optional[str]) -> Optional[TicketData]:
        """
        Validates and immediately consumes a ticket.
        Returns TicketData if valid, or None if invalid/expired/already used.
        Single-use: replaying the same ticket immediately fails.
        """
        if not ticket or not isinstance(ticket, str) or len(ticket.strip()) < 16:
            return None

        clean_ticket = ticket.strip()
        now = time.time()

        with self._lock:
            ticket_data = self._tickets.pop(clean_ticket, None)
            if not ticket_data:
                # Either invalid or already consumed
                return None

            if now > ticket_data.expires_at:
                # Ticket has expired
                return None

            return ticket_data

    def _purge_expired_locked(self, now: float) -> None:
        """Removes expired tickets to prevent memory leaks."""
        expired = [t for t, data in self._tickets.items() if now > data.expires_at]
        for t in expired:
            del self._tickets[t]


ticket_service = TicketService()

