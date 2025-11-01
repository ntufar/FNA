"""
FastAPI application setup for FNA Platform.

Initializes the FastAPI app with middleware, exception handlers,
and route registration.
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from .core.config import get_settings, get_cors_settings
from .core.exceptions import setup_exception_handlers
from .core.logging_config import setup_logging, RequestLoggerMiddleware
from .database import init_database, close_database, check_database_health, setup_vector_environment
from .api.v1.auth import router as auth_router
from .api.v1.companies import router as companies_router
from .api.v1.reports import router as reports_router
from .api.v1.analysis import router as analysis_router
from .api.v1.alerts import router as alerts_router

# Setup logging first
setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager for startup and shutdown events.
    
    Args:
        app: FastAPI application instance
    """
    # Startup
    logger.info("Starting FNA Platform application...")
    
    try:
        # Initialize database
        init_database()
        logger.info("Database initialized successfully")
        
        # Initialize services (can be expanded later)
        await initialize_services()
        logger.info("Services initialized successfully")
        
        logger.info("Application startup completed")
        
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down FNA Platform application...")
    
    try:
        # Close database connections
        close_database()
        logger.info("Database connections closed")
        
        # Cleanup services
        await cleanup_services()
        logger.info("Services cleaned up")
        
        logger.info("Application shutdown completed")
        
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")


async def initialize_services():
    """Initialize application services."""
    # Setup vector environment (pgvector extension and indexes)
    logger.info("Setting up vector environment...")
    vector_setup_results = setup_vector_environment()
    
    if vector_setup_results.get('fallback_mode'):
        logger.warning("Running in JSONB fallback mode - vector search may be slower")
    else:
        logger.info("Vector environment setup completed successfully")
    
    # TODO: Initialize LLM model, embedding service, etc.
    # This will be expanded in later tasks


async def cleanup_services():
    """Cleanup application services."""
    # TODO: Cleanup model resources, cache, etc.
    pass


def create_application() -> FastAPI:
    """
    Create and configure FastAPI application.
    
    Returns:
        FastAPI: Configured application instance
    """
    settings = get_settings()
    
    # Create FastAPI app with custom lifespan
    app = FastAPI(
        title="Financial Narrative Analyzer Platform",
        description="AI-powered platform for analyzing financial report narratives",
        version="1.0.0",
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
        lifespan=lifespan
    )
    
    # Setup middleware
    setup_middleware(app)
    
    # Setup exception handlers
    setup_exception_handlers(app)
    
    # Register routes
    register_routes(app)
    
    # Add health check endpoints
    setup_health_checks(app)
    
    logger.info("FastAPI application created and configured")
    return app


def setup_middleware(app: FastAPI):
    """
    Configure application middleware.
    
    Args:
        app: FastAPI application instance
    """
    settings = get_settings()
    cors_settings = get_cors_settings()
    
    # Request logging middleware (first)
    app.add_middleware(RequestLoggerMiddleware)
    
    # Trusted host middleware for production
    if not settings.debug:
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=["localhost", "127.0.0.1", "*.yourdomain.com"]
        )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_settings["allow_origins"],
        allow_credentials=cors_settings["allow_credentials"],
        allow_methods=cors_settings["allow_methods"],
        allow_headers=cors_settings["allow_headers"],
        expose_headers=["X-Request-ID", "X-Processing-Time"]
    )
    
    # Security headers middleware
    @app.middleware("http")
    async def add_security_headers(request: Request, call_next):
        """Add security headers to all responses."""
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        if not settings.debug:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        return response
    
    # Request ID middleware
    @app.middleware("http")
    async def add_request_id(request: Request, call_next):
        """Add unique request ID to each request."""
        import uuid
        
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        
        # Add to request state for use in handlers
        request.state.request_id = request_id
        
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        
        return response
    
    # Processing time middleware
    @app.middleware("http")
    async def add_process_time(request: Request, call_next):
        """Add processing time header to responses."""
        import time
        
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        
        response.headers["X-Processing-Time"] = str(process_time)
        
        return response
    
    logger.info("Middleware configured successfully")


def register_routes(app: FastAPI):
    """
    Register API routes with the application.
    
    Args:
        app: FastAPI application instance
    """
    # API v1 routes
    app.include_router(
        auth_router,
        prefix="/v1/auth",
        tags=["Authentication"]
    )
    
    app.include_router(
        companies_router,
        prefix="/v1/companies",
        tags=["Companies"]
    )
    
    app.include_router(
        reports_router,
        prefix="/v1/reports",
        tags=["Reports"]
    )
    
    app.include_router(
        analysis_router,
        prefix="/v1/analysis",
        tags=["Analysis"]
    )
    
    app.include_router(
        alerts_router,
        prefix="/v1/alerts",
        tags=["Alerts"]
    )
    
    logger.info("API routes registered successfully")


def setup_health_checks(app: FastAPI):
    """
    Setup health check endpoints.
    
    Args:
        app: FastAPI application instance
    """
    
    @app.get("/health", response_model=Dict[str, Any])
    async def health_check():
        """
        Application health check endpoint.
        
        Returns:
            dict: Health status information
        """
        try:
            # Check database health
            db_health = check_database_health()
            
            # Check overall application health
            health_status = {
                "status": "healthy",
                "version": "1.0.0",
                "service": "fna-platform",
                "database": db_health,
                "timestamp": "2025-10-29T00:00:00Z"  # Will be updated with real timestamp
            }
            
            # If database is not healthy, mark overall as unhealthy
            if db_health.get("status") != "healthy":
                health_status["status"] = "unhealthy"
            
            return health_status
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "service": "fna-platform",
                "timestamp": "2025-10-29T00:00:00Z"
            }
    
    @app.get("/health/ready", response_model=Dict[str, Any])
    async def readiness_check():
        """
        Kubernetes readiness probe endpoint.
        
        Returns:
            dict: Readiness status
        """
        try:
            # Check if all required services are ready
            db_health = check_database_health()
            
            if db_health.get("status") == "healthy":
                return {
                    "status": "ready",
                    "checks": {
                        "database": "ok"
                    }
                }
            else:
                return JSONResponse(
                    status_code=503,
                    content={
                        "status": "not_ready",
                        "checks": {
                            "database": "failed"
                        }
                    }
                )
                
        except Exception as e:
            logger.error(f"Readiness check failed: {e}")
            return JSONResponse(
                status_code=503,
                content={
                    "status": "not_ready",
                    "error": str(e)
                }
            )
    
    @app.get("/health/live", response_model=Dict[str, str])
    async def liveness_check():
        """
        Kubernetes liveness probe endpoint.
        
        Returns:
            dict: Liveness status
        """
        return {"status": "alive"}
    
    logger.info("Health check endpoints configured")


# Create the FastAPI app instance
app = create_application()


# Development server entry point
def run_development_server():
    """Run the development server with hot reload."""
    settings = get_settings()
    
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level=settings.log_level.lower(),
        access_log=True
    )


if __name__ == "__main__":
    run_development_server()
