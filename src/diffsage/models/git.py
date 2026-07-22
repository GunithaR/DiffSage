from dataclasses import dataclass

@dataclass
class GitStatus:
    """Represents the current status of a Git repository."""

    modified: list[str]
    added: list[str]
    deleted: list[str]
    untracked: list[str]

