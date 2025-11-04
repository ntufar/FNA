"""Subscription tier access control middleware.

Enforces subscription tier requirements for API endpoints.
"""

from typing import Optional, Dict, Any
from fastapi import Request, HTTPException, status


class SubscriptionCheckMiddleware:
    """Middleware to check subscription tier requirements."""
    
    def __init__(self, app):
        """Initialize subscription check middleware."""
        self.app = app
        self.tier_hierarchy = {
            "Basic": 0,
            "Pro": 1,
            "Enterprise": 2
        }
    
    async def __call__(self, scope, receive, send):
        """Process request with subscription checks."""
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        request = Request(scope, receive)
        
        # Get user info from request state (set by auth middleware)
        user_tier = request.state.get("subscription_tier", "Basic")
        
        # Check if endpoint requires specific tier
        # This is handled by dependencies in FastAPI, but middleware can add
        # additional checks or logging
        
        # For now, just pass through - tier checking is done via dependencies
        await self.app(scope, receive, send)


def check_subscription_tier(
    required_tier: str,
    user_tier: str
) -> bool:
    """
    Check if user's subscription tier meets requirement.
    
    Args:
        required_tier: Required subscription tier
        user_tier: User's current subscription tier
        
    Returns:
        True if user meets requirement, False otherwise
    """
    tier_hierarchy = {
        "Basic": 0,
        "Pro": 1,
        "Enterprise": 2
    }
    
    required_level = tier_hierarchy.get(required_tier, 0)
    user_level = tier_hierarchy.get(user_tier, 0)
    
    return user_level >= required_level


def get_subscription_middleware():
    """Factory function to create subscription check middleware."""
    return SubscriptionCheckMiddleware

