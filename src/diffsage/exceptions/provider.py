from diffsage.exceptions.base import ProviderError


class AuthenticationError(ProviderError):
    """Raised when authentication with a provider fails."""


class RateLimitError(ProviderError):
    """Raised when a provider rate limit is exceeded."""


class ModelNotFoundError(ProviderError):
    """Raised when the requested model is unavailable."""


class ProviderUnavailableError(ProviderError):
    """Raised when the provider service is unavailable."""


class InvalidRequestError(ProviderError):
    """Raised when a provider rejects a request as invalid for a reason other than
    authentication, such as a prompt that is too long or an unsupported parameter."""
