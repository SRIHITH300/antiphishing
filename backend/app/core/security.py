"""
Security utilities for authentication and input validation
"""
import hashlib
import re
from urllib.parse import urlparse
from typing import Optional


def compute_url_hash(url: str) -> str:
    """
    Compute SHA-256 hash of normalized URL
    
    Args:
        url: URL string
        
    Returns:
        Hexadecimal hash string
    """
    normalized_url = normalize_url(url)
    return hashlib.sha256(normalized_url.encode('utf-8')).hexdigest()


def normalize_url(url: str) -> str:
    """
    Normalize URL for consistent hashing and processing
    
    - Convert to lowercase
    - Remove trailing slashes
    - Ensure scheme is present
    - Remove default ports
    
    Args:
        url: URL string
        
    Returns:
        Normalized URL string
    """
    url = url.strip()
    
    # Add scheme if missing
    if not url.startswith(('http://', 'https://')):
        url = 'http://' + url
    
    # Parse URL
    parsed = urlparse(url)
    
    # Normalize components
    scheme = parsed.scheme.lower()
    netloc = parsed.netloc.lower()
    path = parsed.path.rstrip('/')
    
    # Remove default ports
    if netloc.endswith(':80') and scheme == 'http':
        netloc = netloc[:-3]
    elif netloc.endswith(':443') and scheme == 'https':
        netloc = netloc[:-4]
    
    # Reconstruct URL
    normalized = f"{scheme}://{netloc}{path}"
    
    if parsed.query:
        normalized += f"?{parsed.query}"
    
    return normalized


def validate_url(url: str) -> tuple[bool, Optional[str]]:
    """
    Validate URL format and safety
    
    Args:
        url: URL string
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not url:
        return False, "URL is empty"
    
    if len(url) > 2048:
        return False, "URL is too long (max 2048 characters)"
    
    # Check for valid scheme
    if not url.startswith(('http://', 'https://')):
        return False, "URL must use http or https scheme"
    
    # Basic URL pattern validation
    url_pattern = re.compile(
        r'^https?://'  # scheme
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain
        r'localhost|'  # localhost
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # IP
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE
    )
    
    if not url_pattern.match(url):
        return False, "Invalid URL format"
    
    return True, None


def sanitize_url_for_display(url: str) -> str:
    """
    Sanitize URL for safe display in responses
    
    Args:
        url: URL string
        
    Returns:
        Sanitized URL string
    """
    # Remove any potential XSS vectors
    url = url.replace('<', '&lt;').replace('>', '&gt;')
    return url[:200]  # Truncate for display
