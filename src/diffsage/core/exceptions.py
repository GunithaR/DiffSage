class DiffSageError(Exception):
    """Base exception for all DiffSage errors."""

class ConfigError(DiffSageError):
    """Raised when configuration is invalid."""

class ProviderError(DiffSageError):
    """Raised when an AI provider fails."""

class GitError(DiffSageError):
    """Raised when git operations fail."""