import asyncio
import logging
import math
import re
import time
from collections import defaultdict, deque
from dataclasses import dataclass

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


logger = logging.getLogger("security.rate_limit")
CHAT_PATH = re.compile(r"^/conversations/\d+/chat(?:/resume)?$")
UPLOAD_PATH = re.compile(r"^/\d+/documents$")


@dataclass(frozen=True)
class RateLimitPolicy:
    name: str
    requests: int


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Sliding-window API limiter with endpoint-specific policies."""

    def __init__(
        self,
        app,
        *,
        enabled: bool = True,
        window_seconds: int = 60,
        default_requests: int = 120,
        chat_requests: int = 30,
        upload_requests: int = 10,
    ) -> None:
        super().__init__(app)
        self.enabled = enabled
        self.window_seconds = max(1, window_seconds)
        self.policies = {
            "default": RateLimitPolicy("default", max(1, default_requests)),
            "chat": RateLimitPolicy("chat", max(1, chat_requests)),
            "upload": RateLimitPolicy("upload", max(1, upload_requests)),
        }
        self._requests: dict[str, deque[float]] = defaultdict(deque)
        self._lock = asyncio.Lock()

    def _policy(self, request: Request) -> RateLimitPolicy | None:
        if request.method in {"OPTIONS", "HEAD"} or request.url.path in {
            "/health",
            "/health/db",
            "/docs",
            "/openapi.json",
        }:
            return None
        if request.method == "POST" and CHAT_PATH.fullmatch(request.url.path):
            return self.policies["chat"]
        if request.method == "POST" and UPLOAD_PATH.fullmatch(request.url.path):
            return self.policies["upload"]
        return self.policies["default"]

    async def dispatch(self, request: Request, call_next):
        policy = self._policy(request)
        if not self.enabled or policy is None:
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        key = f"{client_ip}:{policy.name}"
        now = time.monotonic()
        cutoff = now - self.window_seconds

        async with self._lock:
            timestamps = self._requests[key]
            while timestamps and timestamps[0] <= cutoff:
                timestamps.popleft()

            if len(timestamps) >= policy.requests:
                retry_after = max(
                    1,
                    math.ceil(self.window_seconds - (now - timestamps[0])),
                )
                logger.warning(
                    "Rate limit exceeded",
                    extra={
                        "event": "rate_limit.exceeded",
                        "client_ip": client_ip,
                        "policy": policy.name,
                        "limit": policy.requests,
                        "retry_after_seconds": retry_after,
                    },
                )
                return JSONResponse(
                    status_code=429,
                    content={
                        "detail": (
                            "Too many requests. Please wait before trying again."
                        )
                    },
                    headers={
                        "Retry-After": str(retry_after),
                        "X-RateLimit-Limit": str(policy.requests),
                        "X-RateLimit-Remaining": "0",
                    },
                )

            timestamps.append(now)
            remaining = policy.requests - len(timestamps)

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(policy.requests)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(self.window_seconds)
        return response
