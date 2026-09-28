"""In-memory request rate limiter. Disabled in tests."""

from __future__ import annotations

import time
from collections import defaultdict

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.core.config import settings

SKIP_PREFIXES = ("/health", "/docs", "/redoc", "/openapi.json")


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app) -> None:
        super().__init__(app)
        self._hits: dict[str, list[float]] = defaultdict(list)

    async def dispatch(self, request: Request, call_next) -> Response:
        if not settings.rate_limit_enabled:
            return await call_next(request)
        path = request.url.path
        if path in SKIP_PREFIXES or path.startswith("/docs"):
            return await call_next(request)
        key = request.client.host if request.client else "unknown"
        now = time.monotonic()
        window = settings.rate_limit_window_seconds
        recent = [stamp for stamp in self._hits[key] if now - stamp < window]
        if len(recent) >= settings.rate_limit_requests:
            return JSONResponse(
                status_code=429,
                content={
                    "error": {
                        "code": "RATE_LIMIT_EXCEEDED",
                        "message": "Too many requests. Try again shortly.",
                        "details": [],
                    }
                },
            )
        recent.append(now)
        self._hits[key] = recent
        return await call_next(request)
