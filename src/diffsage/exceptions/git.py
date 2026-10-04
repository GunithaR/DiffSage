from diffsage.exceptions.base import GitError


class NotGitRepositoryError(GitError):
    """Raised when the current directory is not a Git repository."""

    default_message = "Not inside a Git repository."


class NoStagedChangesError(GitError):
    """Raised when there are no staged changes to commit."""

    default_message = "No staged changes found. Stage files with 'git add' first."


class BaseBranchNotFoundError(GitError):
    """Raise when a valid pull request base branch cannot be determined."""

    default_message = "Could not determine the base branch."


class RemoteBranchNotFoundError(GitError):
    """Raised when the current branch does not exist on the remote."""

    default_message = "Remote branch does not exist on origin."


class UnpushedChangesError(GitError):
    """Raised when the local branch contains commits not pushed to the remote."""

    default_message = "Your branch contains commits that have not been pushed to origin."


class CommitFailedError(GitError):
    """Raised when `git commit` itself fails, for example when a hook rejects the commit."""
