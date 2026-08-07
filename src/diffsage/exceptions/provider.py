from diffsage.exceptions.base import ProviderError


class AuthenticationError(ProviderError):
    """Raised when authentication with a provider fails."""


class RateLimitError(ProviderError):
    """Raised when a provider rate limit is exceeded."""


class ModelNotFoundError(ProviderError):
    """Raised when the requested model is unavailable."""


class ProviderUnavailableError(ProviderError):
    """Raised when the provider service is unavailable."""
