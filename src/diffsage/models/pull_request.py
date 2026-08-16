from dataclasses import dataclass, field


@dataclass(slots=True)
class PullRequestDraft:
    """Represents a generated pull request draft."""

    title: str
    summary: str
    why: str
    changes: list[str] = field(default_factory=list)
    testing: list[str] = field(default_factory=list)
    risks: list[str] = field(default_factory=list)
    reviewer_focus: list[str] = field(default_factory=list)
    breaking_changes: list[str] = field(default_factory=list)
