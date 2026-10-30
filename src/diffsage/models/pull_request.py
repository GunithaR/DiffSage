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
    # The repository's own pull request template, filled in. When set, it is the whole
    # pull request body and the fixed sections above are unused.
    body: str | None = None

    def to_dict(self) -> dict:
        if self.body is not None:
            return {"title": self.title, "body": self.body}

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
