class DiffSageError(Exception):
    """Base exception for all DiffSage errors.

    Subclasses set `default_message` for when they are raised without one, and
    `exit_code` for the process exit status the CLI reports.
    """

    default_message = "DiffSage could not complete the command."
    exit_code = 1

    def __init__(self, message: str | None = None) -> None:
        super().__init__(message or self.default_message)

    @property
    def message(self) -> str:
        return str(self)


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

    default_message = "Cannot generate a pull request from a detached HEAD."


class SameBranchError(DiffSageError):
    """Raised when the current branch and base branch are the same."""

    default_message = "Current branch and base branch are the same."


class EditorError(DiffSageError):
    """Raised when the user's text editor cannot be launched."""


class ConfigError(DiffSageError):
    """Raised when configuration is invalid."""


class LocalConfigUnavailableError(ConfigError):
    """Raised when local configuration is requested outside a Git repository."""

    default_message = (
        "Local configuration needs a Git repository: it is stored in .diffsage.toml at the "
        "repository root. Run this inside a repository, or use --global."
    )


class UnknownConfigurationKeyError(ConfigError):
    """Raised when configuration key does not exist."""

    def __init__(self, key: str) -> None:
        super().__init__(f"Unknown configuration key: '{key}'")


class InvalidConfigurationValueError(ConfigError):
    """Raised when configuration value is of invalid type."""

    def __init__(self, value: str) -> None:
        super().__init__(f"Invalid configuration value: '{value}'")
