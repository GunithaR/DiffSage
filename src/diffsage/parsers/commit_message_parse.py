from diffsage.models.commit_message import CommitMessage

class CommitMessageParser:
    @staticmethod
    def parse(message: str) -> CommitMessage:
        lines = message.splitlines()

        header = lines[0]
        body = lines[1:]

        header_parts = header.split(":", maxsplit=1)
        prefix = header_parts[0].strip()
        subject = header_parts[1].strip()

        type_part = prefix.split("(", maxsplit=1)[0]
        scope_part = prefix.split("(", maxsplit=1)[1].rstrip(")")
        
        return CommitMessage(
            type=type_part,
            scope=scope_part,
            subject=subject,
            body=body,
        )