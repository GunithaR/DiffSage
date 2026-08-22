class DiffSageError(Exception):
    """Base exception for all DiffSage errors."""


class ProviderError(DiffSageError):
    """Raised when an AI provider fails."""


class GitError(DiffSageError):
    """Raised when git operations fail."""


class InvalidCommitMessageError(DiffSageError):
    """Raised when an AI-generated commit message cannot be parsed."""


class InvalidPullRequestDraftError(DiffSageError):
    """Raised when an AI-generated pull request draft is invalid."""


class DetachedHeadError(DiffSageError):
    """Raised when git repository HEAD is detached."""


class SameBranchError(DiffSageError):
    """Raised when the current branch and base branch are the same."""


class ConfigError(DiffSageError):
    """Raised when configuration is invalid."""


class UnknownConfigurationKeyError(ConfigError):
    """Raised when configuration key does not exist."""

    def __init__(self, key: str) -> None:
        super().__init__(f"Unknown configuration key: '{key}'")


class InvalidConfigurationValueError(ConfigError):
    """Raised when configuration value is of invalid type."""

    def __init__(self, value: str) -> None:
        super().__init__(f"Invalid configuration value: '{value}'")
