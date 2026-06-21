"""Rate limiting for API endpoints."""

import time
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta

from fastapi import Request, HTTPException, status
from app.core import get_logger

logger = get_logger(__name__)


class SimpleRateLimiter:
    """Simple in-memory rate limiter."""
    
    def __init__(
        self,
        requests_per_minute: int = 60,
        burst_size: int = 10,
    ):
        self.requests_per_minute = requests_per_minute
        self.burst_size = burst_size
        self.requests: Dict[str, list] = {}
        self.blocked: Dict[str, datetime] = {}
    
    def _get_key(self, request: Request) -> str:
        """Get rate limit key from request."""
        # Use client IP as key
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        
        if request.client:
            return str(request.client.host)
        
        return "unknown"
    
    def is_allowed(self, request: Request) -> Tuple[bool, Optional[int]]:
        """Check if request is allowed. Returns (allowed, retry_after_seconds)."""
        key = self._get_key(request)
        now = time.time()
        
        # Check if blocked
        if key in self.blocked:
            if datetime.utcnow() < self.blocked[key]:
                retry_after = int((self.blocked[key] - datetime.utcnow()).total_seconds())
                return False, retry_after
            else:
                del self.blocked[key]
        
        # Clean old requests (older than 1 minute)
        if key in self.requests:
            self.requests[key] = [
                ts for ts in self.requests[key]
                if now - ts < 60
            ]
        else:
            self.requests[key] = []
        
        # Check burst limit
        if len(self.requests[key]) >= self.burst_size + self.requests_per_minute:
            # Block for 5 minutes
            self.blocked[key] = datetime.utcnow() + timedelta(minutes=5)
            logger.warning(f"Rate limit exceeded for {key}, blocking for 5 minutes")
            return False, 300
        
        # Check rate limit
        if len(self.requests[key]) >= self.requests_per_minute:
            oldest = self.requests[key][0]
            retry_after = int(60 - (now - oldest)) + 1
            return False, retry_after
        
        # Record request
        self.requests[key].append(now)
        return True, None
    
    def reset(self, request: Request) -> None:
        """Reset rate limit for a request."""
        key = self._get_key(request)
        self.requests.pop(key, None)
        self.blocked.pop(key, None)


# Singleton instances for different endpoints
auth_limiter = SimpleRateLimiter(requests_per_minute=10, burst_size=5)  # Stricter for auth
api_limiter = SimpleRateLimiter(requests_per_minute=60, burst_size=20)   # General API
upload_limiter = SimpleRateLimiter(requests_per_minute=5, burst_size=2)  # Very strict for uploads
# Verification creation fans out to several outbound network calls per request,
# so it is rate limited more aggressively than ordinary reads.
generation_limiter = SimpleRateLimiter(requests_per_minute=10, burst_size=3)


def rate_limit(limiter: SimpleRateLimiter):
    """Build a FastAPI dependency that enforces ``limiter`` for one endpoint.

    Use on expensive routes (e.g. verification creation) to apply a stricter
    limit than the path-based middleware provides.
    """

    async def _dependency(request: Request) -> None:
        allowed, retry_after = limiter.is_allowed(request)
        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please slow down.",
                headers={"Retry-After": str(retry_after)} if retry_after else None,
            )

    return _dependency


async def rate_limit_middleware(request: Request, call_next):
    """Global rate limiting middleware."""
    path = request.url.path
    
    # Skip rate limiting for health checks
    if path == "/health" or path == "/":
        return await call_next(request)
    
    # Select limiter based on path
    if "/auth/" in path:
        limiter = auth_limiter
    elif "/upload" in path:
        limiter = upload_limiter
    else:
        limiter = api_limiter
    
    # Check rate limit
    allowed, retry_after = limiter.is_allowed(request)
    
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded",
            headers={"Retry-After": str(retry_after)} if retry_after else None,
        )
    
    return await call_next(request)
