from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
import time
from typing import Dict


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple in-memory rate limiter per IP/user.

    Not suitable for multi-process production. Use Redis for production.
    """

    def __init__(self, app, max_requests: int = 60, window_seconds: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window = window_seconds
        self.sensitive_paths = ("/auth/login", "/auth/register", "/api/score", "/api/leaderboard", "/api/profile")
        # store: key -> [timestamps]
        self._requests: Dict[str, list] = {}

    async def dispatch(self, request: Request, call_next):
        # Key by user (if authenticated) or by client IP
        client = request.client.host if request.client else "unknown"
        auth = request.headers.get("authorization") or ""
        key = auth.split()[-1] if auth else client

        if request.url.path in self.sensitive_paths:
            self.max_requests = 20
        else:
            self.max_requests = 60

        now = time.time()
        bucket = self._requests.get(key) or []
        # Remove expired
        window_start = now - self.window
        bucket = [ts for ts in bucket if ts > window_start]
        if len(bucket) >= self.max_requests:
            # Too many requests
            return JSONResponse({"detail": "Rate limit exceeded"}, status_code=429)

        bucket.append(now)
        self._requests[key] = bucket

        response = await call_next(request)
        return response
