from diffsage.exceptions.base import ProviderError


class AuthenticationError(ProviderError):
    """Raised when authentication with a provider fails."""


class RateLimitError(ProviderError):
    """Raised when a provider rate limit is exceeded.

    `retry_after` is how many seconds the provider asked the client to wait before
    trying again, when it said.
    """

    default_message = "The AI provider's rate limit was exceeded."

    def __init__(self, message: str | None = None, retry_after: float | None = None) -> None:
        super().__init__(message)
        self.retry_after = retry_after


class ModelNotFoundError(ProviderError):
    """Raised when the requested model is unavailable."""


class ProviderUnavailableError(ProviderError):
    """Raised when the provider service is unavailable."""


class InvalidRequestError(ProviderError):
    """Raised when a provider rejects a request as invalid for a reason other than
    authentication, such as a prompt that is too long or an unsupported parameter."""


class EmptyResponseError(ProviderError):
    """Raised when a provider returns a reply with no text."""

    default_message = "The AI provider returned an empty reply."


class ContentBlockedError(ProviderError):
    """Raised when a provider blocks the prompt or stops the reply for policy reasons."""


class ResponseTruncatedError(ProviderError):
    """Raised when a reply is cut off by the output token limit."""
