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

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "summary": self.summary,
            "why": self.why,
            "changes": self.changes,
            "testing": self.testing,
            "risks": self.risks,
            "reviewer_focus": self.reviewer_focus,
            "breaking_changes": self.breaking_changes,
        }
