"""
Logging configuration for FNA Platform.

Sets up structured logging with appropriate formatters and handlers
for development and production environments.
"""

import logging
import logging.config
import sys
from typing import Dict, Any
import json
from datetime import datetime

import structlog
from pythonjsonlogger import jsonlogger

from .config import get_settings


class CustomJSONFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter with additional context."""
    
    def add_fields(self, log_record, record, message_dict):
        """Add custom fields to log record."""
        super().add_fields(log_record, record, message_dict)
        
        # Add timestamp if not present
        if not log_record.get('timestamp'):
            log_record['timestamp'] = datetime.utcnow().isoformat()
        
        # Add service information
        log_record['service'] = 'fna-platform'
        log_record['version'] = '1.0.0'
        
        # Add log level
        if log_record.get('level'):
            log_record['level'] = log_record['level'].upper()
        else:
            log_record['level'] = record.levelname


def setup_logging():
    """
    Configure application logging based on environment settings.
    
    Sets up both standard Python logging and structured logging with structlog.
    """
    settings = get_settings()
    
    # Configure based on environment
    if settings.debug:
        setup_development_logging(settings)
    else:
        setup_production_logging(settings)
    
    # Configure structlog
    setup_structlog(settings)
    
    # Test logging setup
    logger = logging.getLogger(__name__)
    logger.info(
        "Logging system initialized",
        extra={
            "log_level": settings.log_level,
            "debug_mode": settings.debug
        }
    )


def setup_development_logging(settings):
    """Configure logging for development environment."""
    
    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "detailed": {
                "format": "%(asctime)s | %(name)-20s | %(levelname)-8s | %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S"
            },
            "simple": {
                "format": "%(levelname)s: %(message)s"
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": settings.log_level,
                "formatter": "detailed",
                "stream": sys.stdout
            },
            "file": {
                "class": "logging.FileHandler",
                "level": "DEBUG",
                "formatter": "detailed",
                "filename": "logs/development.log",
                "mode": "a"
            }
        },
        "loggers": {
            # Application loggers
            "src": {
                "level": "DEBUG",
                "handlers": ["console", "file"],
                "propagate": False
            },
            # FastAPI loggers
            "fastapi": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False
            },
            "uvicorn": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False
            },
            "uvicorn.access": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False
            },
            # SQLAlchemy loggers
            "sqlalchemy.engine": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False
            },
            "sqlalchemy.pool": {
                "level": "WARNING",
                "handlers": ["console"],
                "propagate": False
            },
            # External library loggers
            "requests": {
                "level": "WARNING",
                "handlers": ["console"],
                "propagate": False
            },
            "urllib3": {
                "level": "WARNING",
                "handlers": ["console"],
                "propagate": False
            }
        },
        "root": {
            "level": settings.log_level,
            "handlers": ["console"]
        }
    }
    
    # Ensure logs directory exists
    import os
    os.makedirs("logs", exist_ok=True)
    
    logging.config.dictConfig(logging_config)


def setup_production_logging(settings):
    """Configure logging for production environment."""
    
    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "json": {
                "()": CustomJSONFormatter,
                "format": "%(timestamp)s %(level)s %(name)s %(message)s"
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": settings.log_level,
                "formatter": "json",
                "stream": sys.stdout
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "INFO",
                "formatter": "json",
                "filename": "logs/application.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5
            },
            "error_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "ERROR",
                "formatter": "json",
                "filename": "logs/error.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5
            }
        },
        "loggers": {
            # Application loggers
            "src": {
                "level": "INFO",
                "handlers": ["console", "file", "error_file"],
                "propagate": False
            },
            # FastAPI loggers
            "fastapi": {
                "level": "INFO",
                "handlers": ["console", "file"],
                "propagate": False
            },
            "uvicorn": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False
            },
            "uvicorn.access": {
                "level": "INFO",
                "handlers": ["file"],  # Access logs to file only
                "propagate": False
            },
            # External library loggers (quiet in production)
            "requests": {
                "level": "ERROR",
                "handlers": ["console"],
                "propagate": False
            },
            "urllib3": {
                "level": "ERROR",
                "handlers": ["console"],
                "propagate": False
            },
            "sqlalchemy": {
                "level": "WARNING",
                "handlers": ["console"],
                "propagate": False
            }
        },
        "root": {
            "level": settings.log_level,
            "handlers": ["console"]
        }
    }
    
    # Ensure logs directory exists
    import os
    os.makedirs("logs", exist_ok=True)
    
    logging.config.dictConfig(logging_config)


def setup_structlog(settings):
    """Configure structured logging with structlog."""
    
    # Configure processors based on environment
    if settings.debug:
        processors = [
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.dev.ConsoleRenderer(colors=True)  # Colored output for dev
        ]
    else:
        processors = [
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()  # JSON output for production
        ]
    
    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def get_logger(name: str = None) -> structlog.stdlib.BoundLogger:
    """
    Get a configured structlog logger.
    
    Args:
        name: Logger name (defaults to calling module name)
        
    Returns:
        Configured structlog logger instance
    """
    return structlog.get_logger(name)


class RequestLoggerMiddleware:
    """
    Middleware to log HTTP requests and responses.
    """
    
    def __init__(self, app):
        self.app = app
        self.logger = get_logger("request_logger")
    
    async def __call__(self, scope, receive, send):
        """Process HTTP request and log details."""
        
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        
        # Extract request information
        method = scope["method"]
        path = scope["path"]
        client_ip = self._get_client_ip(scope)
        
        # Start timer
        import time
        start_time = time.time()
        
        # Process request
        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                # Log response
                status_code = message["status"]
                processing_time = time.time() - start_time
                
                # Determine log level based on status code
                if status_code >= 500:
                    log_level = "error"
                elif status_code >= 400:
                    log_level = "warning"
                else:
                    log_level = "info"
                
                # Log request/response
                getattr(self.logger, log_level)(
                    "HTTP request processed",
                    method=method,
                    path=path,
                    status_code=status_code,
                    client_ip=client_ip,
                    processing_time=processing_time
                )
            
            return await send(message)
        
        return await self.app(scope, receive, send_wrapper)
    
    def _get_client_ip(self, scope) -> str:
        """Extract client IP from request scope."""
        # Check for X-Forwarded-For header (proxy/load balancer)
        headers = dict(scope.get("headers", []))
        forwarded_for = headers.get(b"x-forwarded-for")
        if forwarded_for:
            return forwarded_for.decode().split(",")[0].strip()
        
        # Check for X-Real-IP header
        real_ip = headers.get(b"x-real-ip")
        if real_ip:
            return real_ip.decode()
        
        # Fall back to direct client connection
        client = scope.get("client")
        if client:
            return client[0]
        
        return "unknown"


# Performance monitoring utilities
def log_function_call(func_name: str = None):
    """
    Decorator to log function calls and performance.
    
    Args:
        func_name: Optional custom function name for logging
        
    Returns:
        Decorated function with logging
    """
    def decorator(func):
        import functools
        import time
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            logger = get_logger("performance")
            name = func_name or f"{func.__module__}.{func.__name__}"
            
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                
                logger.info(
                    "Function call completed",
                    function=name,
                    execution_time=execution_time,
                    success=True
                )
                return result
                
            except Exception as e:
                execution_time = time.time() - start_time
                
                logger.error(
                    "Function call failed",
                    function=name,
                    execution_time=execution_time,
                    error=str(e),
                    success=False
                )
                raise
        
        return wrapper
    return decorator
