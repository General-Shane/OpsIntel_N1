from typing import Optional, Dict, Any

class ServiceNowError(Exception):
    """Base exception for all ServiceNow integration operations."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class ServiceNowAuthError(ServiceNowError):
    """Authentication or OAuth2 token exchange failure."""
    pass


class ServiceNowRateLimitError(ServiceNowError):
    """HTTP 429 Rate Limit exceeded."""
    def __init__(self, message: str, retry_after: Optional[float] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, details)
        self.retry_after = retry_after or 5.0


class ServiceNowValidationError(ServiceNowError):
    """Payload schema or business validation error."""
    pass


class ServiceNowTransientError(ServiceNowError):
    """Transient server error (500, 502, 503, 504, timeout) eligible for retry."""
    def __init__(self, message: str, status_code: Optional[int] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, details)
        self.status_code = status_code


class ServiceNowPermanentError(ServiceNowError):
    """Permanent client error (400, 403, 404) that should not be retried blindly."""
    def __init__(self, message: str, status_code: Optional[int] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, details)
        self.status_code = status_code


class ServiceNowNotFoundError(ServiceNowPermanentError):
    """Entity not found in ServiceNow table."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=404, details=details)
