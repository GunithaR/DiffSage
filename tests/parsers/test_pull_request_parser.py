import json

import pytest

from diffsage.exceptions import InvalidPullRequestDraftError
from diffsage.parsers.pull_request_parser import PullRequestParser


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
