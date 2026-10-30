from diffsage.exit_codes import ExitCode


class DiffSageError(Exception):
    """Base exception for all DiffSage errors.

    Subclasses set `default_message` for when they are raised without one, and
    `exit_code` for the process exit status the CLI reports.
    """

    default_message = "DiffSage could not complete the command."
    exit_code: int = ExitCode.ERROR

    def __init__(self, message: str | None = None) -> None:
        super().__init__(message or self.default_message)

    @property
    def message(self) -> str:
        return str(self)


class ProviderError(DiffSageError):
    """Raised when an AI provider fails."""

    exit_code = ExitCode.AI_PROVIDER


class GitError(DiffSageError):
    """Raised when git operations fail, or the repository is not in a usable state."""

    exit_code = ExitCode.GIT


class InvalidCommitMessageError(DiffSageError):
    """Raised when an AI-generated commit message cannot be parsed."""

    exit_code = ExitCode.AI_OUTPUT


class InvalidPullRequestDraftError(DiffSageError):
    """Raised when an AI-generated pull request draft is invalid."""

    exit_code = ExitCode.AI_OUTPUT


class DetachedHeadError(GitError):
    """Raised when git repository HEAD is detached."""

    default_message = (
        "Cannot generate a pull request from a detached HEAD. Switch to a branch first: "
        "git switch <branch>"
    )


class SameBranchError(GitError):
    """Raised when the current branch and base branch are the same."""

    default_message = "Current branch and base branch are the same."


class NoTerminalError(DiffSageError):
    """Raised when a command would ask for confirmation but there is no terminal to ask in,
    as in CI, git hooks and pipes."""

    exit_code = ExitCode.USAGE


class EditorError(DiffSageError):
    """Raised when the user's text editor cannot be launched."""


class ConfigError(DiffSageError):
    """Raised when configuration is invalid."""

    exit_code = ExitCode.CONFIGURATION


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
    """Raised when a configuration value is rejected."""

    def __init__(self, value: str, key: str | None = None, reason: str | None = None) -> None:
        message = f"Invalid value '{value}'"

        if key is not None:
            message += f" for {key}"

        if reason is not None:
            message += f": {reason}"

        super().__init__(message)
