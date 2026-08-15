class ServiceError(Exception):
    """Base exception for all service-layer failures."""


class NotFoundError(ServiceError):
    """Raised when an expected entity cannot be found."""


class ConflictError(ServiceError):
    """Raised when an operation conflicts with existing data."""


class ValidationError(ServiceError):
    """Raised when business-rule validation fails."""


class AuthenticationError(ServiceError):
    """Raised when credentials are missing or invalid (maps to HTTP 401)."""


class AuthorizationError(ServiceError):
    """Raised when an authenticated user lacks permission for an action (maps to HTTP 403)."""
