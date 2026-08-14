"""
Security utilities including sliding-window rate limiting and admin token authentication.
"""

from __future__ import annotations

import time
from collections import defaultdict, deque
from threading import Lock
from typing import Optional

from fastapi import HTTPException, Header, Request

from core.config import settings


class RateLimiter:
    """In-memory IP sliding-window rate limiter."""

    def __init__(self, limit: int, window_sec: int):
        self.limit = limit
        self.window_sec = window_sec
        self.buckets: dict[str, deque] = defaultdict(deque)
        self.lock = Lock()

    def check(self, request: Request) -> None:
        client_ip = request.client.host if request.client else "unknown"
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            client_ip = forwarded.split(",")[0].strip()

        now = time.time()
        with self.lock:
            q = self.buckets[client_ip]
            cutoff = now - self.window_sec
            while q and q[0] < cutoff:
                q.popleft()
            if len(q) >= self.limit:
                raise HTTPException(
                    status_code=429,
                    detail="Too many requests. Please wait a moment before sending another message.",
                )
            q.append(now)


rate_limiter = RateLimiter(
    limit=settings.chat_rate_limit,
    window_sec=settings.chat_rate_window_sec,
)


def verify_admin_token(
    x_admin_token: Optional[str] = Header(default=None),
    authorization: Optional[str] = Header(default=None),
) -> bool:
    """Enforces admin token check if ADMIN_TOKEN is configured in the environment."""
    expected = settings.admin_token.strip()
    if not expected:
        # In open/dev mode with no admin token configured, allow local admin calls
        return True

    token = (x_admin_token or "").strip()
    if not token and authorization:
        parts = authorization.strip().split()
        if len(parts) == 2 and parts[0].lower() == "bearer":
            token = parts[1]

    if token != expected:
        raise HTTPException(
            status_code=401,
            detail="Admin token missing or invalid. Set X-Admin-Token or Authorization: Bearer <token>",
        )
    return True
