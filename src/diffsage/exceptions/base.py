class DiffSageError(Exception):
    """Base exception for all DiffSage errors."""


class ConfigError(DiffSageError):
    """Raised when configuration is invalid."""


class UnknownConfigurationKeyError(ConfigError):
    """Raised when configuration key does not exist."""

    def __init__(self, key: str) -> None:
        super().__init__(f"Unknown configuration key: '{key}'")


class ProviderError(DiffSageError):
    """Raised when an AI provider fails."""


class GitError(DiffSageError):
    """Raised when git operations fail."""
