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
    """Represents a commit history in a Git repository"""

    hash: str
    author: str
    message: str
    date: datetime

