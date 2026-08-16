from diffsage.exceptions.base import GitError


class NotGitRepositoryError(GitError):
    """Raised when the current directory is not a Git repository."""


class NoStagedChangesError(GitError):
    """Raised when there are no staged changes to commit."""


class BaseBranchNotFoundError(GitError):
    """Raise when a valid pull request base branch cannot be determined."""