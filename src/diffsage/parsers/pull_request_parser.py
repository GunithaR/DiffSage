import json

from diffsage.exceptions import InvalidPullRequestDraftError
from diffsage.models.pull_request import PullRequestDraft


class PullRequestParser:
    def parse(self, content: str) -> PullRequestDraft:
        try:
            data = json.loads(content)
        except json.JSONDecodeError as exc:
            raise InvalidPullRequestDraftError("AI response is not valid JSON.") from exc

        if not isinstance(data, dict):
            raise InvalidPullRequestDraftError("AI response must be a JSON object.")

        required_fields = {
            "title",
            "summary",
            "why",
            "changes",
            "testing",
            "risks",
            "reviewer_focus",
            "breaking_changes",
        }

        if set(data) != required_fields:
            raise InvalidPullRequestDraftError(
                "AI response contains invalid or missing pull request fields."
            )

        if not isinstance(data["title"], str):
            raise InvalidPullRequestDraftError("Pull request title must be a string.")

        if not isinstance(data["summary"], str):
            raise InvalidPullRequestDraftError("Pull request summary must be a string.")

        if not isinstance(data["why"], str):
            raise InvalidPullRequestDraftError("Pull request why field must be a string.")

        list_fields = {
            "changes",
            "testing",
            "risks",
            "reviewer_focus",
            "breaking_changes",
        }

        for field in list_fields:
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
