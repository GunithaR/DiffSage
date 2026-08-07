from diffsage.exceptions import InvalidCommitMessageError
from diffsage.models.commit_message import CommitMessage


class CommitMessageParser:
    @staticmethod
    def parse(message: str) -> CommitMessage:
        lines = message.splitlines()

        if not lines:
            raise InvalidCommitMessageError("Commit message is empty.")

        header = lines[0]
        body = lines[1:]

        if ":" not in header:
            raise InvalidCommitMessageError(
                "Commit message header must use '<type>: <subject>' format."
            )

        header_parts = header.split(":", maxsplit=1)
        prefix = header_parts[0].strip()
        subject = header_parts[1].strip()

        if "(" in prefix:
            type_part = prefix.split("(", maxsplit=1)[0]
            scope_part = prefix.split("(", maxsplit=1)[1].rstrip(")")
        else:
            type_part = prefix
            scope_part = None

        if not type_part:
            raise InvalidCommitMessageError("Commit message type is missing.")

        if not subject:
            raise InvalidCommitMessageError("Commit message subject is missing.")

        return CommitMessage(
            type=type_part,
            scope=scope_part,
            subject=subject,
            body=body,
        )