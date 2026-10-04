from dataclasses import dataclass, field


@dataclass(slots=True)
class CommitMessage:
    """A parsed Conventional Commit message."""

    type: str | None = None
    scope: str | None = None
    subject: str = ""
    body: list[str] = field(default_factory=list)
    breaking: bool = False

    @property
    def header(self) -> str:
        scope = f"({self.scope})" if self.scope else ""
        breaking = "!" if self.breaking else ""
        return f"{self.type}{scope}{breaking}: {self.subject}"

    def to_text(self) -> str:
        """The message exactly as it should be committed."""

        if not self.body:
            return self.header

        return f"{self.header}\n\n" + "\n".join(self.body)
