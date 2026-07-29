from dataclasses import dataclass, field


@dataclass(slots=True)
class CommitMessage:
    type: str | None = None
    scope: str | None = None
    subject: str = ""
    body: list[str] = field(default_factory=list)