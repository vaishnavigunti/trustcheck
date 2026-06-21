"""
Custom application exceptions.
"""


class TrustCheckException(Exception):
    """Base exception for TrustCheck application."""

    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class AuthenticationError(TrustCheckException):
    """Authentication related errors."""

    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, status_code=401)


class AuthorizationError(TrustCheckException):
    """Authorization related errors."""

    def __init__(self, message: str = "Not authorized"):
        super().__init__(message, status_code=403)


class NotFoundError(TrustCheckException):
    """Resource not found errors."""

    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, status_code=404)


class ValidationError(TrustCheckException):
    """Input validation errors."""

    def __init__(self, message: str = "Validation error"):
        super().__init__(message, status_code=422)


class VerificationError(TrustCheckException):
    """Verification process errors."""

    def __init__(self, message: str = "Verification failed"):
        super().__init__(message, status_code=500)


class FileUploadError(TrustCheckException):
    """File upload related errors."""

    def __init__(self, message: str = "File upload failed"):
        super().__init__(message, status_code=400)


class RateLimitError(TrustCheckException):
    """Rate limiting errors."""

    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(message, status_code=429)
