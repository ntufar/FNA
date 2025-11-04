"""
Security utilities for FNA Platform.

Provides input sanitization, SQL injection prevention, and security helpers.
"""

import re
import html
import logging
from typing import Optional, List
from urllib.parse import quote, unquote

logger = logging.getLogger(__name__)


def sanitize_input(input_str: str, max_length: Optional[int] = None) -> str:
    """
    Sanitize user input to prevent XSS and injection attacks.
    
    Args:
        input_str: Input string to sanitize
        max_length: Maximum allowed length (None for no limit)
        
    Returns:
        str: Sanitized string
    """
    if not isinstance(input_str, str):
        return ""
    
    # Remove null bytes
    sanitized = input_str.replace('\x00', '')
    
    # Strip whitespace
    sanitized = sanitized.strip()
    
    # Encode HTML entities to prevent XSS
    sanitized = html.escape(sanitized)
    
    # Limit length if specified
    if max_length and len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
        logger.warning(f"Input truncated to {max_length} characters")
    
    return sanitized


def sanitize_ticker_symbol(ticker: str) -> str:
    """
    Sanitize and validate ticker symbol.
    
    Args:
        ticker: Ticker symbol to sanitize
        
    Returns:
        str: Sanitized ticker symbol (uppercase, alphanumeric only)
        
    Raises:
        ValueError: If ticker is invalid
    """
    if not isinstance(ticker, str):
        raise ValueError("Ticker symbol must be a string")
    
    # Remove whitespace and convert to uppercase
    ticker = ticker.strip().upper()
    
    # Validate format: 1-5 alphanumeric characters
    if not re.match(r'^[A-Z0-9]{1,5}$', ticker):
        raise ValueError(f"Invalid ticker symbol format: {ticker}")
    
    return ticker


def sanitize_email(email: str) -> str:
    """
    Sanitize and validate email address.
    
    Args:
        email: Email address to sanitize
        
    Returns:
        str: Sanitized email address (lowercase)
        
    Raises:
        ValueError: If email is invalid
    """
    if not isinstance(email, str):
        raise ValueError("Email must be a string")
    
    # Remove whitespace and convert to lowercase
    email = email.strip().lower()
    
    # Basic email validation regex
    email_pattern = r'^[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}$'
    if not re.match(email_pattern, email):
        raise ValueError(f"Invalid email format: {email}")
    
    # Prevent injection attempts
    if any(char in email for char in ['<', '>', '"', "'", ';', '--', '/*']):
        raise ValueError(f"Email contains invalid characters: {email}")
    
    return email


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to prevent path traversal attacks.
    
    Args:
        filename: Filename to sanitize
        
    Returns:
        str: Sanitized filename
    """
    if not isinstance(filename, str):
        return "unnamed"
    
    # Remove path separators and dangerous characters
    sanitized = re.sub(r'[<>:"/\\|?*]', '', filename)
    
    # Remove leading/trailing dots and spaces
    sanitized = sanitized.strip('. ')
    
    # Limit length
    if len(sanitized) > 255:
        sanitized = sanitized[:255]
    
    # Ensure it's not empty
    if not sanitized:
        sanitized = "unnamed"
    
    return sanitized


def validate_sql_safe(identifier: str) -> bool:
    """
    Validate that an identifier is safe for use in SQL queries.
    
    Note: SQLAlchemy ORM already provides protection, but this is an
    additional safety check for raw SQL queries.
    
    Args:
        identifier: Identifier to validate
        
    Returns:
        bool: True if safe, False otherwise
    """
    if not isinstance(identifier, str):
        return False
    
    # Check for SQL injection patterns
    dangerous_patterns = [
        r'--',  # SQL comment
        r'/\*',  # Multi-line comment start
        r'\*/',  # Multi-line comment end
        r"';",  # Statement termination
        r'";',  # Statement termination
        r'DROP\s+TABLE',  # DROP TABLE
        r'DELETE\s+FROM',  # DELETE
        r'TRUNCATE',  # TRUNCATE
        r'EXEC\s*\(',  # EXEC
        r'EXECUTE\s*\(',  # EXECUTE
        r'UNION\s+SELECT',  # UNION SELECT
    ]
    
    identifier_upper = identifier.upper()
    for pattern in dangerous_patterns:
        if re.search(pattern, identifier_upper, re.IGNORECASE):
            logger.warning(f"Potentially dangerous SQL pattern detected: {pattern}")
            return False
    
    return True


def sanitize_url(url: str) -> str:
    """
    Sanitize URL to prevent SSRF and other attacks.
    
    Args:
        url: URL to sanitize
        
    Returns:
        str: Sanitized URL
        
    Raises:
        ValueError: If URL is invalid or dangerous
    """
    if not isinstance(url, str):
        raise ValueError("URL must be a string")
    
    url = url.strip()
    
    # Only allow http and https protocols
    if not url.startswith(('http://', 'https://')):
        raise ValueError(f"URL must use http:// or https:// protocol: {url}")
    
    # Block localhost and private IP ranges (SSRF protection)
    dangerous_hosts = [
        'localhost',
        '127.0.0.1',
        '0.0.0.0',
        '::1',
        '10.',
        '172.16.',
        '172.17.',
        '172.18.',
        '172.19.',
        '172.20.',
        '172.21.',
        '172.22.',
        '172.23.',
        '172.24.',
        '172.25.',
        '172.26.',
        '172.27.',
        '172.28.',
        '172.29.',
        '172.30.',
        '172.31.',
        '192.168.',
    ]
    
    url_lower = url.lower()
    for host in dangerous_hosts:
        if host in url_lower:
            raise ValueError(f"URL contains blocked host pattern: {host}")
    
    return url


def validate_file_extension(filename: str, allowed_extensions: List[str]) -> bool:
    """
    Validate file extension against allowed list.
    
    Args:
        filename: Filename to validate
        allowed_extensions: List of allowed extensions (e.g., ['.pdf', '.html'])
        
    Returns:
        bool: True if extension is allowed
    """
    if not filename:
        return False
    
    # Get file extension
    if '.' not in filename:
        return False
    
    ext = filename.lower().rsplit('.', 1)[1]
    allowed = [ext.lower().lstrip('.') for ext in allowed_extensions]
    
    return ext in allowed


def validate_file_size(file_size: int, max_size: int) -> bool:
    """
    Validate file size against maximum allowed size.
    
    Args:
        file_size: File size in bytes
        max_size: Maximum allowed size in bytes
        
    Returns:
        bool: True if file size is within limit
    """
    return 0 < file_size <= max_size


def generate_secure_filename(original_filename: str, prefix: str = "") -> str:
    """
    Generate a secure filename by sanitizing and adding timestamp.
    
    Args:
        original_filename: Original filename
        prefix: Optional prefix for the filename
        
    Returns:
        str: Secure filename
    """
    # Sanitize original filename
    sanitized = sanitize_filename(original_filename)
    
    # Get extension
    if '.' in sanitized:
        name, ext = sanitized.rsplit('.', 1)
    else:
        name, ext = sanitized, ''
    
    # Generate secure filename with timestamp
    from datetime import datetime
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    
    if prefix:
        secure_name = f"{prefix}_{timestamp}_{name}"
    else:
        secure_name = f"{timestamp}_{name}"
    
    if ext:
        secure_name = f"{secure_name}.{ext}"
    
    return secure_name


def rate_limit_key(user_id: str, endpoint: str) -> str:
    """
    Generate a rate limit key for a user and endpoint.
    
    Args:
        user_id: User identifier
        endpoint: API endpoint
        
    Returns:
        str: Rate limit key
    """
    # Sanitize inputs
    user_id = sanitize_input(user_id, max_length=100)
    endpoint = sanitize_input(endpoint, max_length=200)
    
    return f"rate_limit:{user_id}:{endpoint}"

