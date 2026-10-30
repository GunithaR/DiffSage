from diffsage.exceptions.base import DiffSageError
from diffsage.exit_codes import ExitCode


class GitHubError(DiffSageError):
    """Raised when a GitHub operation fails."""

    exit_code = ExitCode.GITHUB


class GitHubCLIUnavailableError(GitHubError):
    """Raised when the GitHub CLI is not installed."""


class GitHubAuthenticationError(GitHubError):
    """Raised when the user is not authenticated with GitHub."""

    exit_code = ExitCode.CREDENTIALS


class PullRequestExistsError(GitHubError):
    """Raised when the branch already has an open pull request into the base branch."""
