"""Rate limiting middleware for FNA API.

Implements per-tier rate limiting based on subscription tier:
- Basic: 100 requests/hour
- Pro: 500 requests/hour
- Enterprise: 2000 requests/hour
"""

import time
from collections import defaultdict
from typing import Dict, Optional

from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware


class RateLimiter:
    """Simple in-memory rate limiter using sliding window."""
    
    def __init__(self):
        """Initialize rate limiter with request tracking."""
        self.requests: Dict[str, list] = defaultdict(list)
        self.limits = {
            "Basic": 100,      # 100 requests per hour
            "Pro": 500,        # 500 requests per hour
            "Enterprise": 2000  # 2000 requests per hour
        }
    
    def is_allowed(self, user_id: str, tier: str = "Basic") -> tuple[bool, Optional[int]]:
        """
        Check if request is allowed for user.
        
        Args:
            user_id: User identifier
            tier: Subscription tier
            
        Returns:
            Tuple of (is_allowed, remaining_requests)
        """
        current_time = time.time()
        window_start = current_time - 3600  # 1 hour window
        
        # Get user's request history
        user_requests = self.requests[user_id]
        
        # Remove requests outside the time window
        user_requests[:] = [req_time for req_time in user_requests if req_time > window_start]
        
        # Get limit for tier
        limit = self.limits.get(tier, 100)
        
        # Check if limit exceeded
        if len(user_requests) >= limit:
            remaining = 0
            return False, remaining
        
        # Record this request
        user_requests.append(current_time)
        remaining = limit - len(user_requests)
        
        return True, remaining
    
    def get_remaining(self, user_id: str, tier: str = "Basic") -> int:
        """Get remaining requests for user."""
        current_time = time.time()
        window_start = current_time - 3600
        
        user_requests = self.requests[user_id]
        user_requests[:] = [req_time for req_time in user_requests if req_time > window_start]
        
        limit = self.limits.get(tier, 100)
        return max(0, limit - len(user_requests))


# Global rate limiter instance
rate_limiter = RateLimiter()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware for rate limiting."""
    
    def __init__(self, app, exempt_paths: Optional[list] = None):
        """
        Initialize rate limiting middleware.
        
        Args:
            app: FastAPI application
            exempt_paths: List of path prefixes to exempt from rate limiting
        """
        super().__init__(app)
        self.exempt_paths = exempt_paths or ["/docs", "/openapi.json", "/redoc", "/health"]
    
    async def dispatch(self, request: Request, call_next):
        """Process request with rate limiting."""
        # Skip rate limiting for exempt paths
        if any(request.url.path.startswith(path) for path in self.exempt_paths):
            return await call_next(request)
        
        # Get user info from request state (set by auth middleware)
        user_id = request.state.get("user_id")
        tier = request.state.get("subscription_tier", "Basic")
        
        # If no user, skip rate limiting (public endpoints)
        if not user_id:
            return await call_next(request)
        
        # Check rate limit
        is_allowed, remaining = rate_limiter.is_allowed(user_id, tier)
        
        if not is_allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded for {tier} tier. Limit: {rate_limiter.limits.get(tier, 100)} requests/hour",
                headers={
                    "X-RateLimit-Limit": str(rate_limiter.limits.get(tier, 100)),
                    "X-RateLimit-Remaining": "0",
                    "Retry-After": "3600"
                }
            )
        
        # Add rate limit headers to response
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(rate_limiter.limits.get(tier, 100))
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        
        return response


def get_rate_limit_middleware(exempt_paths: Optional[list] = None):
    """Factory function to create rate limit middleware."""
    return lambda app: RateLimitMiddleware(app, exempt_paths)

