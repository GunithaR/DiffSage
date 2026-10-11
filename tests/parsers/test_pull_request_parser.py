import json
from dataclasses import fields

import pytest

from diffsage.exceptions import InvalidPullRequestDraftError
from diffsage.models.pull_request import PullRequestDraft
from diffsage.parsers.pull_request_parser import PULL_REQUEST_DRAFT_SCHEMA, PullRequestParser


def test_parse_valid_pull_request_response() -> None:
    content = json.dumps(
        {
            "title": "Add pull request generation",
            "summary": "Adds Git-first pull request generation.",
            "why": "Provides structured reviewer-facing pull request content.",
            "changes": [
                "Add pull request context collection.",
                "Add deterministic pull request analysis.",
            ],
            "testing": [
                "Added unit tests for pull request analysis.",
            ],
            "risks": [
                "Changes affect pull request generation workflow.",
            ],
            "reviewer_focus": [
                "Review pull request analysis and generation.",
            ],
            "breaking_changes": [],
        }
    )

    parser = PullRequestParser()

    draft = parser.parse(content)

    assert draft.title == "Add pull request generation"
    assert draft.summary == "Adds Git-first pull request generation."
    assert draft.why == ("Provides structured reviewer-facing pull request content.")
    assert draft.changes == [
        "Add pull request context collection.",
        "Add deterministic pull request analysis.",
    ]
    assert draft.testing == [
        "Added unit tests for pull request analysis.",
    ]
    assert draft.risks == [
        "Changes affect pull request generation workflow.",
    ]
    assert draft.reviewer_focus == [
        "Review pull request analysis and generation.",
    ]
    assert draft.breaking_changes == []


def test_parse_invalid_json_raises_error() -> None:
    parser = PullRequestParser()

    with pytest.raises(InvalidPullRequestDraftError):
        parser.parse("not valid json")


def test_parse_non_object_json_raises_error() -> None:
    parser = PullRequestParser()

    with pytest.raises(InvalidPullRequestDraftError):
        parser.parse("[]")


def test_parse_missing_required_field_raises_error() -> None:
    content = json.dumps(
        {
            "title": "Add feature",
            "summary": "Summary",
            "why": "Why",
            "changes": [],
            "testing": [],
            "risks": [],
            "reviewer_focus": [],
        }
    )

    parser = PullRequestParser()

    with pytest.raises(InvalidPullRequestDraftError):
        parser.parse(content)


def test_parse_unexpected_field_raises_error() -> None:
    content = json.dumps(
        {
            "title": "Add feature",
            "summary": "Summary",
            "why": "Why",
            "changes": [],
            "testing": [],
            "risks": [],
            "reviewer_focus": [],
            "breaking_changes": [],
            "labels": [],
        }
    )

    parser = PullRequestParser()

    with pytest.raises(InvalidPullRequestDraftError):
        parser.parse(content)


def test_parse_invalid_title_type_raises_error() -> None:
    content = json.dumps(
        {
            "title": 123,
            "summary": "Summary",
            "why": "Why",
            "changes": [],
            "testing": [],
            "risks": [],
            "reviewer_focus": [],
            "breaking_changes": [],
        }
    )

    parser = PullRequestParser()

    with pytest.raises(InvalidPullRequestDraftError):
        parser.parse(content)


def test_parse_invalid_changes_type_raises_error() -> None:
    content = json.dumps(
        {
            "title": "Add feature",
            "summary": "Summary",
            "why": "Why",
            "changes": "Add feature",
            "testing": [],
            "risks": [],
            "reviewer_focus": [],
            "breaking_changes": [],
        }
    )

    parser = PullRequestParser()

    with pytest.raises(InvalidPullRequestDraftError):
        parser.parse(content)


def test_parse_list_with_non_string_item_raises_error() -> None:
    content = json.dumps(
        {
            "title": "Add feature",
            "summary": "Summary",
            "why": "Why",
            "changes": ["Valid change", 123],
            "testing": [],
            "risks": [],
            "reviewer_focus": [],
            "breaking_changes": [],
        }
    )

    parser = PullRequestParser()

    with pytest.raises(InvalidPullRequestDraftError):
        parser.parse(content)


def test_draft_schema_matches_the_draft_model() -> None:
    """The schema sent to the AI and the model the parser builds must not drift apart."""

    names = [field.name for field in fields(PullRequestDraft)]

    assert list(PULL_REQUEST_DRAFT_SCHEMA["properties"]) == names
    assert PULL_REQUEST_DRAFT_SCHEMA["required"] == names


def test_a_draft_that_follows_the_schema_parses() -> None:
    draft = {
        name: "text" if spec["type"] == "string" else ["item"]
        for name, spec in PULL_REQUEST_DRAFT_SCHEMA["properties"].items()
    }

    assert PullRequestParser().parse(json.dumps(draft)).to_dict() == draft


def valid_draft() -> dict:
    return {
        "title": "Add retries",
        "summary": "Retries failed requests.",
        "why": "Rate limits are common on the free tier.",
        "changes": ["Retry 429s with backoff."],
        "testing": ["Unit tests for the retry loop."],
        "risks": [],
        "reviewer_focus": [],
        "breaking_changes": [],
    }


@pytest.mark.parametrize(
    "wrap",
    [
        lambda body: f"```json\n{body}\n```",
        lambda body: f"```\n{body}\n```\n",
        lambda body: f"Here is the pull request draft:\n\n```json\n{body}\n```",
        lambda body: f"Sure! {{see below}}\n{body}\nLet me know if you want changes.",
    ],
    ids=["json-fence", "bare-fence", "preamble-and-fence", "prose-with-stray-brace"],
)
def test_parse_finds_the_draft_inside_fences_and_prose(wrap) -> None:
    """Regression: a reply wrapped in a ```json fence was rejected as invalid JSON."""

    draft = valid_draft()

    parsed = PullRequestParser().parse(wrap(json.dumps(draft, indent=2)))

    assert parsed.to_dict() == draft


def test_parse_keeps_braces_and_fences_inside_string_values() -> None:
    draft = valid_draft()
    draft["summary"] = "Adds `retry()` and a ```python``` example: {attempt} } {"

    parsed = PullRequestParser().parse(f"```json\n{json.dumps(draft)}\n```")

    assert parsed.summary == draft["summary"]


@pytest.mark.parametrize(
    "content",
    ['```json\n{"title": "unterminated"\n```', "No JSON here at all.", "```\n```"],
)
def test_parse_still_rejects_replies_without_a_complete_json_object(content) -> None:
    with pytest.raises(InvalidPullRequestDraftError, match="not valid JSON"):
        PullRequestParser().parse(content)


def test_parse_validates_the_object_found_inside_a_fence() -> None:
    draft = valid_draft()
    del draft["why"]

    with pytest.raises(InvalidPullRequestDraftError, match="invalid or missing"):
        PullRequestParser().parse(f"```json\n{json.dumps(draft)}\n```")
