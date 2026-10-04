import re

from diffsage.exceptions import InvalidCommitMessageError
from diffsage.models.commit_message import CommitMessage

CONVENTIONAL_TYPES = (
    "build",
    "chore",
    "ci",
    "docs",
    "feat",
    "fix",
    "perf",
    "refactor",
    "revert",
    "style",
    "test",
)

# <type>[(<scope>)][!]: <subject>
HEADER = re.compile(
    r"^(?P<type>[A-Za-z]+)"
    r"(?:\((?P<scope>[^()\s][^()]*)\))?"
    r"(?P<breaking>!)?"
    r":\s*(?P<subject>\S.*)$"
)
FENCE = re.compile(r"^\s*```")


def _without_fences(lines: list[str]) -> list[str]:
    """Drop Markdown code fence lines (```, ```text, ...) that models often add."""

    return [line for line in lines if not FENCE.match(line)]


def _without_preamble(lines: list[str]) -> list[str]:
    """Skip leading chatter such as "Here is your commit message:" when a valid
    Conventional Commit header follows it."""

    for index, line in enumerate(lines):
        match = HEADER.match(line.strip())

        if match and match.group("type").lower() in CONVENTIONAL_TYPES:
            return lines[index:]

    return lines


def _trim_blank_lines(lines: list[str]) -> list[str]:
    start, end = 0, len(lines)

    while start < end and not lines[start].strip():
        start += 1

    while end > start and not lines[end - 1].strip():
        end -= 1

    return [line.rstrip() for line in lines[start:end]]


class CommitMessageParser:
    @staticmethod
    def parse(message: str) -> CommitMessage:
        lines = _trim_blank_lines(_without_preamble(_without_fences(message.splitlines())))

        if not lines:
            raise InvalidCommitMessageError("Commit message is empty.")

        header = lines[0].strip()
        match = HEADER.match(header)

        if match is None:
            raise InvalidCommitMessageError(
                "The first line must look like '<type>[(scope)][!]: <subject>', for example "
                f"'feat(cli): add version flag'. Got: '{header}'"
            )

        commit_type = match.group("type").lower()

        if commit_type not in CONVENTIONAL_TYPES:
            raise InvalidCommitMessageError(
                f"'{commit_type}' is not a Conventional Commit type. Use one of: "
                + ", ".join(CONVENTIONAL_TYPES)
                + "."
            )

        return CommitMessage(
            type=commit_type,
            scope=match.group("scope").strip() if match.group("scope") else None,
            subject=match.group("subject").strip(),
            body=_trim_blank_lines(lines[1:]),
            breaking=match.group("breaking") is not None,
        )
