"""
Core package for FNA Platform.

Contains configuration, security, model management, and other core utilities.
"""

from .config import get_settings, get_cors_settings, get_upload_settings

__all__ = [
    "get_settings",
    "get_cors_settings", 
    "get_upload_settings",
]
