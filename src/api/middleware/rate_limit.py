from typing import Dict
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from time import time
from collections import defaultdict
import asyncio


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware for API endpoints."""

    def __init__(
        self,
        app,
        requests_per_minute: int = 60,
        requests_per_hour: int = 1000,
    ):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        self.clients: Dict[str, Dict] = defaultdict(lambda: {
            "minute": [],
            "hour": []
        })
        # Start cleanup task
        asyncio.create_task(self._cleanup_old_entries())

    async def dispatch(self, request: Request, call_next):
        # Get client IP
        client_ip = request.client.host

        # Check if this is a public API route
        if not request.url.path.startswith("/api/public"):
            return await call_next(request)

        current_time = time()

        # Clean old requests
        self.clients[client_ip]["minute"] = [
            t for t in self.clients[client_ip]["minute"]
            if current_time - t < 60
        ]
        self.clients[client_ip]["hour"] = [
            t for t in self.clients[client_ip]["hour"]
            if current_time - t < 3600
        ]

        # Check rate limits
        if len(self.clients[client_ip]["minute"]) >= self.requests_per_minute:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": "Rate limit exceeded. Maximum 60 requests per minute allowed.",
                    "retry_after": 60
                },
                headers={"Retry-After": "60"}
            )

        if len(self.clients[client_ip]["hour"]) >= self.requests_per_hour:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": "Rate limit exceeded. Maximum 1000 requests per hour allowed.",
                    "retry_after": 3600
                },
                headers={"Retry-After": "3600"}
            )

        # Record this request
        self.clients[client_ip]["minute"].append(current_time)
        self.clients[client_ip]["hour"].append(current_time)

        response = await call_next(request)

        # Add rate limit headers
        response.headers["X-RateLimit-Limit-Minute"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining-Minute"] = str(
            self.requests_per_minute - len(self.clients[client_ip]["minute"])
        )
        response.headers["X-RateLimit-Limit-Hour"] = str(self.requests_per_hour)
        response.headers["X-RateLimit-Remaining-Hour"] = str(
            self.requests_per_hour - len(self.clients[client_ip]["hour"])
        )

        return response

    async def _cleanup_old_entries(self):
        """Periodically cleanup old entries to prevent memory leak."""
        while True:
            await asyncio.sleep(300)  # Every 5 minutes
            current_time = time()

            # Remove clients with no recent requests
            clients_to_remove = []
            for client_ip, data in self.clients.items():
                if (not data["hour"] or
                    current_time - max(data["hour"]) > 3600):
                    clients_to_remove.append(client_ip)

            for client_ip in clients_to_remove:
                del self.clients[client_ip]