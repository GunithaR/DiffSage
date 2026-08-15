from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class GitStatus:
    """Represents the current status of a Git repository."""

    modified: list[str]
    added: list[str]
    deleted: list[str]
    untracked: list[str]


@dataclass(slots=True)
class GitCommit:
    """Represents a single commit in a Git repository"""

    hash: str
    author: str
    message: str
    date: datetime


@dataclass(slots=True)
class CommitContext:
    """Represents the information needed to generate a commit message."""

    branch: str
    staged_diff: str
    unstaged_diff: str
    recent_commits: list[GitCommit]


@dataclass(slots=True)
class PullRequestContext:
    """Represents the information needed to generate a pull request."""

    current_branch: str
    base_branch: str
    merge_base: str
    commits: list[GitCommit]
    changed_files: list[str]
    diff: str
