"""API version 1 routes for FNA backend."""

from fastapi import APIRouter
from .auth import router as auth_router
from .companies import router as companies_router
from .reports import router as reports_router
from .analysis import router as analysis_router
from .alerts import router as alerts_router

# Create main v1 router
api_router = APIRouter()

# Include all route modules
api_router.include_router(auth_router, prefix="/auth", tags=["authentication"])
api_router.include_router(companies_router, prefix="/companies", tags=["companies"])
api_router.include_router(reports_router, prefix="/reports", tags=["reports"])
api_router.include_router(analysis_router, prefix="/analysis", tags=["analysis"])
api_router.include_router(alerts_router, prefix="/alerts", tags=["alerts"])

__all__ = ["api_router"]
