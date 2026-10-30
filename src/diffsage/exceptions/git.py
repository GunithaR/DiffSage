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


class RemoteAheadError(GitError):
    """Raised when origin has commits on the branch that the local branch does not."""

    default_message = "Origin has commits on this branch that your local branch does not have."


class BranchesDivergedError(GitError):
    """Raised when the local branch and its origin copy each have commits the other lacks."""

    default_message = "Your local branch and its copy on origin have diverged."


class RemoteUnavailableError(GitError):
    """Raised when origin cannot be reached to check a branch."""

    default_message = "Could not reach origin."


class FetchFailedError(GitError):
    """Raised when `git fetch` cannot update a branch from origin."""

    default_message = "git fetch failed."


class CommitFailedError(GitError):
    """Raised when `git commit` itself fails, for example when a hook rejects the commit."""
