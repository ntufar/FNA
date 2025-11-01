"""
Application configuration management for FNA Platform.

Handles environment variables, database settings, and application config
using Pydantic settings management.
"""

import os
from functools import lru_cache
from typing import Optional, List

from pydantic import Field, validator, ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    Uses Pydantic for validation and type conversion.
    Environment variables can be prefixed with FNA_ for namespacing.
    """
    
    # Database Configuration
    database_url: str = Field(
        default="postgresql://postgres:qwerty123@localhost:5432/fna_development",
        description="PostgreSQL database connection URL"
    )
    
    # LLM Configuration (LM Studio API)
    model_name: str = Field(
        default="qwen/qwen3-4b-2507",
        description="LLM model identifier"
    )
    model_api_url: str = Field(
        default="http://127.0.0.1:1234",
        description="LM Studio API base URL"
    )
    model_api_timeout: int = Field(
        default=300,
        description="LM Studio API request timeout in seconds"
    )
    model_max_tokens: int = Field(
        default=512,
        description="Maximum tokens for LLM generation"
    )
    model_temperature: float = Field(
        default=0.1,
        description="LLM temperature for generation randomness"
    )
    model_top_p: float = Field(
        default=0.9,
        description="LLM top-p for nucleus sampling"
    )
    
    # SEC.gov API Configuration
    sec_user_agent: str = Field(
        default="FNACompany contact@fnacompany.com",
        description="User-Agent string for SEC API requests"
    )
    sec_request_rate_limit: int = Field(
        default=10,
        description="SEC API requests per second limit"
    )
    
    # Security Configuration
    secret_key: str = Field(
        default="dev-secret-key-change-in-production",
        description="Secret key for JWT token signing"
    )
    jwt_expire_hours: int = Field(
        default=24,
        description="JWT token expiration time in hours"
    )
    jwt_refresh_expire_days: int = Field(
        default=7,
        description="JWT refresh token expiration in days"
    )
    jwt_algorithm: str = Field(
        default="HS256",
        description="JWT token signing algorithm"
    )
    
    # Application Configuration
    debug: bool = Field(
        default=False,
        description="Enable debug mode for development"
    )
    log_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)"
    )
    cors_origins: List[str] = Field(
        default=["http://localhost:5173", "http://localhost:3000"],
        description="Allowed CORS origins"
    )
    cors_credentials: bool = Field(
        default=True,
        description="Allow credentials in CORS requests"
    )
    
    # File Upload Configuration
    max_upload_size: int = Field(
        default=52_428_800,  # 50MB
        description="Maximum file upload size in bytes"
    )
    allowed_file_types: List[str] = Field(
        default=[".pdf", ".html", ".txt", ".xml", ".xbrl"],
        description="Allowed file extensions for uploads"
    )
    upload_directory: str = Field(
        default="uploads",
        description="Directory for storing uploaded files"
    )
    
    # Rate Limiting Configuration
    rate_limit_per_minute: int = Field(
        default=60,
        description="API requests per minute per user"
    )
    rate_limit_burst: int = Field(
        default=10,
        description="Burst allowance for rate limiting"
    )
    
    # Performance Configuration
    max_concurrent_analyses: int = Field(
        default=5,
        description="Maximum concurrent sentiment analyses"
    )
    analysis_timeout_seconds: int = Field(
        default=60,
        description="Maximum time allowed for document analysis"
    )
    
    # Monitoring Configuration
    enable_metrics: bool = Field(
        default=True,
        description="Enable application metrics collection"
    )
    metrics_port: int = Field(
        default=9090,
        description="Port for metrics endpoint"
    )
    
    @validator('database_url')
    def validate_database_url(cls, v):
        """Validate database URL format."""
        if not v.startswith(('postgresql://', 'postgres://')):
            raise ValueError('Database URL must be a PostgreSQL connection string')
        return v
    
    @validator('log_level')
    def validate_log_level(cls, v):
        """Validate logging level."""
        valid_levels = {'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'}
        if v.upper() not in valid_levels:
            raise ValueError(f'Log level must be one of: {", ".join(valid_levels)}')
        return v.upper()
    
    @validator('model_temperature')
    def validate_temperature(cls, v):
        """Validate LLM temperature range."""
        if not 0.0 <= v <= 2.0:
            raise ValueError('Temperature must be between 0.0 and 2.0')
        return v
    
    @validator('model_top_p')
    def validate_top_p(cls, v):
        """Validate LLM top_p range."""
        if not 0.0 <= v <= 1.0:
            raise ValueError('Top-p must be between 0.0 and 1.0')
        return v
    
    @validator('cors_origins', pre=True)
    def validate_cors_origins(cls, v):
        """Convert string to list for CORS origins."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(',')]
        return v
    
    @validator('allowed_file_types', pre=True)
    def validate_file_types(cls, v):
        """Convert string to list for file types."""
        if isinstance(v, str):
            return [ext.strip() for ext in v.split(',')]
        return v
    
    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        env_prefix="",  # Can be set to "FNA_" for namespacing
        protected_namespaces=('settings_',)  # Allow model_ fields by changing protected namespace
    )


class DevelopmentSettings(Settings):
    """Development-specific settings."""
    debug: bool = True
    log_level: str = "DEBUG"
    cors_origins: List[str] = [
        "http://localhost:5173", 
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000"
    ]


class ProductionSettings(Settings):
    """Production-specific settings."""
    debug: bool = False
    log_level: str = "INFO"
    
    @validator('secret_key')
    def validate_production_secret_key(cls, v):
        """Ensure secret key is not default in production."""
        if v == "dev-secret-key-change-in-production":
            raise ValueError('Must set secure SECRET_KEY in production')
        if len(v) < 32:
            raise ValueError('Secret key must be at least 32 characters long')
        return v


@lru_cache()
def get_settings() -> Settings:
    """
    Get application settings with caching.
    
    Returns appropriate settings class based on environment.
    Uses LRU cache to avoid repeated environment variable reads.
    
    Returns:
        Settings: Application configuration instance
    """
    environment = os.getenv("ENVIRONMENT", "development").lower()
    
    if environment == "production":
        return ProductionSettings()
    elif environment == "testing":
        # Override some settings for testing
        settings = DevelopmentSettings()
        settings.database_url = "postgresql://postgres:qwerty123@localhost:5432/fna_test"
        return settings
    else:
        # Default to development
        return DevelopmentSettings()


def get_database_url() -> str:
    """
    Get database URL for the current environment.
    
    Returns:
        str: Database connection URL
    """
    return get_settings().database_url


def get_cors_settings() -> dict:
    """
    Get CORS configuration for FastAPI.
    
    Returns:
        dict: CORS middleware configuration
    """
    settings = get_settings()
    return {
        "allow_origins": settings.cors_origins,
        "allow_credentials": settings.cors_credentials,
        "allow_methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
        "allow_headers": ["*"],
    }


def get_upload_settings() -> dict:
    """
    Get file upload configuration.
    
    Returns:
        dict: Upload configuration settings
    """
    settings = get_settings()
    return {
        "max_size": settings.max_upload_size,
        "allowed_types": settings.allowed_file_types,
        "upload_dir": settings.upload_directory,
    }
