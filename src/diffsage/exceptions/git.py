class NotGitRepositoryError(Exception):
    """Raised when the current directory is not a Git repository."""

class NoStagedChangesError(Exception):
    """Raised when there are no staged changes to commit."""