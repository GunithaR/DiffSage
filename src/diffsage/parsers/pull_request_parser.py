import json
from typing import Any

from diffsage.exceptions import InvalidPullRequestDraftError
from diffsage.models.pull_request import PullRequestDraft

_TEXT_FIELDS = ("title", "summary", "why")
_LIST_FIELDS = ("changes", "testing", "risks", "reviewer_focus", "breaking_changes")

# JSON Schema of a pull request draft, sent to providers that can enforce it.
PULL_REQUEST_DRAFT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        **{name: {"type": "string"} for name in _TEXT_FIELDS},
        **{name: {"type": "array", "items": {"type": "string"}} for name in _LIST_FIELDS},
    },
    "required": [*_TEXT_FIELDS, *_LIST_FIELDS],
}


def _load_json(content: str) -> Any:
    """Parse the reply as JSON, falling back to the first JSON object inside it.

    Providers with a JSON mode return bare JSON. Others (and edits) may wrap it in a
    ```json code fence or add a sentence before or after it; the fallback decodes the
    first complete object from each "{" in turn, so braces or fences inside string
    values cannot cut it short.
    """

    try:
        return json.loads(content)
    except json.JSONDecodeError as error:
        decoder = json.JSONDecoder()
        start = content.find("{")

        while start != -1:
            try:
                data, _end = decoder.raw_decode(content, start)
                return data
            except json.JSONDecodeError:
                start = content.find("{", start + 1)

        raise InvalidPullRequestDraftError("The pull request draft is not valid JSON.") from error


class PullRequestParser:
    def parse(self, content: str) -> PullRequestDraft:
        data = _load_json(content)

        if not isinstance(data, dict):
            raise InvalidPullRequestDraftError("The pull request draft must be a JSON object.")

        required = PULL_REQUEST_DRAFT_SCHEMA["required"]
        missing = [name for name in required if name not in data]
        unexpected = [name for name in data if name not in required]

        if missing or unexpected:
            problems = []

            if missing:
                problems.append("missing " + ", ".join(missing))

            if unexpected:
                problems.append("unexpected " + ", ".join(unexpected))

            raise InvalidPullRequestDraftError(
                f"The pull request draft has invalid fields: {'; '.join(problems)}."
            )

        if not isinstance(data["title"], str):
            raise InvalidPullRequestDraftError("Pull request title must be a string.")

        if not isinstance(data["summary"], str):
            raise InvalidPullRequestDraftError("Pull request summary must be a string.")

        if not isinstance(data["why"], str):
            raise InvalidPullRequestDraftError("Pull request why field must be a string.")

        for field in _LIST_FIELDS:
            if not isinstance(data[field], list):
                raise InvalidPullRequestDraftError(f"Pull request {field} field must be a list.")

            if not all(isinstance(item, str) for item in data[field]):
                raise InvalidPullRequestDraftError(
                    f"Pull request {field} must contain only strings."
                )

        return PullRequestDraft(
            title=data["title"],
            summary=data["summary"],
            why=data["why"],
            changes=data["changes"],
            testing=data["testing"],
            risks=data["risks"],
            reviewer_focus=data["reviewer_focus"],
            breaking_changes=data["breaking_changes"],
        )
