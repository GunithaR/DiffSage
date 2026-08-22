from diffsage.exceptions.base import DiffSageError


class GitHubError(DiffSageError):
    """Raised when a GitHub operation fails."""


class GitHubCLIUnavailableError(GitHubError):
    """Raised when the GitHub CLI is not installed."""


class GitHubAuthenticationError(GitHubError):
    """Raised when the user is not authenticated with GitHub."""
