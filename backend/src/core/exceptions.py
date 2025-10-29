"""
Custom exceptions and error handling for FNA Platform.

Defines application-specific exceptions and FastAPI exception handlers
for consistent error responses and logging.
"""

import logging
import traceback
from typing import Any, Dict, Optional, Union

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy.exc import SQLAlchemyError
import structlog

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)


# Base Application Exceptions
class FNAException(Exception):
    """
    Base exception class for all FNA application exceptions.
    
    Provides consistent error structure and logging.
    """
    
    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    ):
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
        self.status_code = status_code
        super().__init__(self.message)
        
        # Log exception when created
        logger.error(
            "FNA Exception raised",
            error_code=self.error_code,
            message=self.message,
            details=self.details,
            status_code=self.status_code
        )


# Authentication & Authorization Exceptions
class AuthenticationError(FNAException):
    """Raised when authentication fails."""
    
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(
            message=message,
            error_code="AUTH_FAILED",
            status_code=status.HTTP_401_UNAUTHORIZED
        )


class AuthorizationError(FNAException):
    """Raised when user lacks required permissions."""
    
    def __init__(self, message: str = "Access denied"):
        super().__init__(
            message=message,
            error_code="ACCESS_DENIED",
            status_code=status.HTTP_403_FORBIDDEN
        )


class InvalidTokenError(AuthenticationError):
    """Raised when JWT token is invalid or expired."""
    
    def __init__(self, message: str = "Invalid or expired token"):
        super().__init__(message)
        self.error_code = "INVALID_TOKEN"


class InsufficientPermissionsError(AuthorizationError):
    """Raised when user's subscription tier is insufficient."""
    
    def __init__(self, required_tier: str, current_tier: str):
        message = f"Requires {required_tier} subscription, current: {current_tier}"
        super().__init__(message)
        self.error_code = "INSUFFICIENT_PERMISSIONS"
        self.details = {
            "required_tier": required_tier,
            "current_tier": current_tier
        }


# Data & Validation Exceptions
class ValidationError(FNAException):
    """Raised when data validation fails."""
    
    def __init__(self, message: str, field: Optional[str] = None):
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            details={"field": field} if field else {},
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
        )


class NotFoundError(FNAException):
    """Raised when requested resource is not found."""
    
    def __init__(self, resource: str, identifier: str):
        message = f"{resource} with identifier '{identifier}' not found"
        super().__init__(
            message=message,
            error_code="RESOURCE_NOT_FOUND",
            details={"resource": resource, "identifier": identifier},
            status_code=status.HTTP_404_NOT_FOUND
        )


class DuplicateResourceError(FNAException):
    """Raised when trying to create a resource that already exists."""
    
    def __init__(self, resource: str, field: str, value: str):
        message = f"{resource} with {field} '{value}' already exists"
        super().__init__(
            message=message,
            error_code="DUPLICATE_RESOURCE",
            details={"resource": resource, "field": field, "value": value},
            status_code=status.HTTP_409_CONFLICT
        )


# File & Processing Exceptions
class FileProcessingError(FNAException):
    """Raised when file processing fails."""
    
    def __init__(self, message: str, filename: Optional[str] = None):
        super().__init__(
            message=message,
            error_code="FILE_PROCESSING_ERROR",
            details={"filename": filename} if filename else {},
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
        )


class UnsupportedFileTypeError(FileProcessingError):
    """Raised when uploaded file type is not supported."""
    
    def __init__(self, file_type: str, allowed_types: list):
        message = f"File type '{file_type}' not supported. Allowed: {', '.join(allowed_types)}"
        super().__init__(message)
        self.error_code = "UNSUPPORTED_FILE_TYPE"
        self.details = {
            "file_type": file_type,
            "allowed_types": allowed_types
        }


class FileTooLargeError(FileProcessingError):
    """Raised when uploaded file exceeds size limit."""
    
    def __init__(self, file_size: int, max_size: int):
        message = f"File size {file_size} bytes exceeds limit of {max_size} bytes"
        super().__init__(message)
        self.error_code = "FILE_TOO_LARGE"
        self.details = {
            "file_size": file_size,
            "max_size": max_size
        }


# External Service Exceptions
class ExternalServiceError(FNAException):
    """Raised when external service call fails."""
    
    def __init__(self, service: str, message: str):
        super().__init__(
            message=f"{service} service error: {message}",
            error_code="EXTERNAL_SERVICE_ERROR",
            details={"service": service},
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE
        )


class SECAPIError(ExternalServiceError):
    """Raised when SEC.gov API request fails."""
    
    def __init__(self, message: str):
        super().__init__("SEC.gov", message)
        self.error_code = "SEC_API_ERROR"


class ModelInferenceError(ExternalServiceError):
    """Raised when LLM inference fails."""
    
    def __init__(self, message: str):
        super().__init__("LLM", message)
        self.error_code = "MODEL_INFERENCE_ERROR"


# Rate Limiting Exception
class RateLimitExceededError(FNAException):
    """Raised when API rate limit is exceeded."""
    
    def __init__(self, limit: int, window: str):
        message = f"Rate limit exceeded: {limit} requests per {window}"
        super().__init__(
            message=message,
            error_code="RATE_LIMIT_EXCEEDED",
            details={"limit": limit, "window": window},
            status_code=status.HTTP_429_TOO_MANY_REQUESTS
        )


# Database Exception
class DatabaseError(FNAException):
    """Raised when database operation fails."""
    
    def __init__(self, message: str, operation: Optional[str] = None):
        super().__init__(
            message=f"Database error: {message}",
            error_code="DATABASE_ERROR",
            details={"operation": operation} if operation else {},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# FastAPI Exception Handlers
async def fna_exception_handler(request: Request, exc: FNAException) -> JSONResponse:
    """
    Handle custom FNA exceptions.
    
    Args:
        request: FastAPI request object
        exc: FNA exception instance
        
    Returns:
        JSONResponse: Formatted error response
    """
    logger.error(
        "FNA exception occurred",
        path=request.url.path,
        method=request.method,
        error_code=exc.error_code,
        message=exc.message,
        details=exc.details,
        status_code=exc.status_code
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.error_code,
                "message": exc.message,
                "details": exc.details,
            },
            "request_id": request.headers.get("X-Request-ID"),
        }
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """
    Handle FastAPI HTTP exceptions.
    
    Args:
        request: FastAPI request object
        exc: HTTP exception instance
        
    Returns:
        JSONResponse: Formatted error response
    """
    logger.warning(
        "HTTP exception occurred",
        path=request.url.path,
        method=request.method,
        status_code=exc.status_code,
        detail=exc.detail
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": "HTTP_ERROR",
                "message": exc.detail,
                "details": {},
            },
            "request_id": request.headers.get("X-Request-ID"),
        }
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """
    Handle Pydantic validation errors.
    
    Args:
        request: FastAPI request object
        exc: Validation exception instance
        
    Returns:
        JSONResponse: Formatted validation error response
    """
    errors = []
    for error in exc.errors():
        errors.append({
            "field": " -> ".join(str(x) for x in error["loc"]),
            "message": error["msg"],
            "type": error["type"]
        })
    
    logger.warning(
        "Validation error occurred",
        path=request.url.path,
        method=request.method,
        errors=errors
    )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Request validation failed",
                "details": {"validation_errors": errors},
            },
            "request_id": request.headers.get("X-Request-ID"),
        }
    )


async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    """
    Handle SQLAlchemy database errors.
    
    Args:
        request: FastAPI request object
        exc: SQLAlchemy exception instance
        
    Returns:
        JSONResponse: Formatted database error response
    """
    logger.error(
        "Database error occurred",
        path=request.url.path,
        method=request.method,
        error=str(exc),
        traceback=traceback.format_exc()
    )
    
    # Don't expose internal database errors to clients
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "DATABASE_ERROR",
                "message": "A database error occurred",
                "details": {},
            },
            "request_id": request.headers.get("X-Request-ID"),
        }
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handle unexpected exceptions.
    
    Args:
        request: FastAPI request object
        exc: Generic exception instance
        
    Returns:
        JSONResponse: Formatted generic error response
    """
    logger.error(
        "Unexpected exception occurred",
        path=request.url.path,
        method=request.method,
        error=str(exc),
        traceback=traceback.format_exc()
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred",
                "details": {},
            },
            "request_id": request.headers.get("X-Request-ID"),
        }
    )


def setup_exception_handlers(app):
    """
    Register all exception handlers with FastAPI app.
    
    Args:
        app: FastAPI application instance
    """
    # Custom FNA exceptions
    app.add_exception_handler(FNAException, fna_exception_handler)
    
    # Standard HTTP exceptions
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    
    # Validation errors
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    
    # Database errors
    app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)
    
    # Generic exceptions (catch-all)
    app.add_exception_handler(Exception, generic_exception_handler)


# Utility functions
def handle_database_error(operation: str):
    """
    Decorator to handle database errors in service functions.
    
    Args:
        operation: Description of the database operation
        
    Returns:
        Decorated function that handles SQLAlchemy errors
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except SQLAlchemyError as e:
                raise DatabaseError(str(e), operation)
        return wrapper
    return decorator


def log_performance(operation: str):
    """
    Decorator to log function performance metrics.
    
    Args:
        operation: Description of the operation being measured
        
    Returns:
        Decorated function that logs execution time
    """
    import time
    
    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                logger.info(
                    "Operation completed successfully",
                    operation=operation,
                    execution_time=execution_time,
                    function=func.__name__
                )
                return result
            except Exception as e:
                execution_time = time.time() - start_time
                logger.error(
                    "Operation failed",
                    operation=operation,
                    execution_time=execution_time,
                    function=func.__name__,
                    error=str(e)
                )
                raise
        return wrapper
    return decorator
