import pytest

from diffsage.exceptions import InvalidCommitMessageError
from diffsage.models.commit_message import CommitMessage
from diffsage.parsers.commit_message_parser import CONVENTIONAL_TYPES, CommitMessageParser

parse = CommitMessageParser.parse


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("feat: add greeting", CommitMessage("feat", None, "add greeting")),
        ("fix(cli): handle empty input", CommitMessage("fix", "cli", "handle empty input")),
        ("feat!: drop v1", CommitMessage("feat", None, "drop v1", breaking=True)),
        (
            "feat(api)!: drop v1 endpoints",
            CommitMessage("feat", "api", "drop v1 endpoints", breaking=True),
        ),
        ("refactor(config/loader): split", CommitMessage("refactor", "config/loader", "split")),
        ("FIX: upper-case type", CommitMessage("fix", None, "upper-case type")),
        ("docs: link https://example.com", CommitMessage("docs", None, "link https://example.com")),
    ],
)
def test_headers_are_parsed(text, expected) -> None:
    """Regression: 'feat(api)!:' gave scope 'api)!' and 'feat!:' gave type 'feat!'."""

    assert parse(text) == expected


def test_body_keeps_its_lines_without_surrounding_blank_lines() -> None:
    message = parse("feat: add banner\n\n\n- Add banner.\n- Show it.\n\n")

    assert message.body == ["- Add banner.", "- Show it."]
    assert message.to_text() == "feat: add banner\n\n- Add banner.\n- Show it."


@pytest.mark.parametrize(
    "text",
    [
        "```\nfeat: add greeting\n```",
        "```text\nfeat: add greeting\n```",
        "Here is a commit message for your changes:\n\nfeat: add greeting",
        "Sure! Here you go:\n```\nfeat: add greeting\n```\nLet me know if you want changes.",
    ],
)
def test_code_fences_and_preamble_are_removed(text) -> None:
    """Regression: replies wrapped in ``` or preceded by a sentence were rejected."""

    assert parse(text).header == "feat: add greeting"


def test_trailing_chatter_after_a_fence_stays_in_the_body() -> None:
    """Only leading chatter is removed; anything after the header is the user's body."""

    message = parse("```\nfeat: add greeting\n```\nLet me know if you want changes.")

    assert message.body == ["Let me know if you want changes."]


@pytest.mark.parametrize(
    "text",
    [
        "Here is your commit message: fix stuff",
        "feat(): empty scope",
        "feat add greeting",
        "feat:",
        "(cli): missing type",
    ],
)
def test_invalid_headers_are_rejected_with_an_example(text) -> None:
    with pytest.raises(InvalidCommitMessageError) as error:
        parse(text)

    assert "for example 'feat(cli): add version flag'" in str(error.value)


@pytest.mark.parametrize("commit_type", ["wip", "feature", "update"])
def test_unknown_types_are_rejected_with_the_allowed_list(commit_type) -> None:
    with pytest.raises(InvalidCommitMessageError) as error:
        parse(f"{commit_type}: do something")

    assert f"'{commit_type}' is not a Conventional Commit type" in str(error.value)
    assert ", ".join(CONVENTIONAL_TYPES) in str(error.value)


@pytest.mark.parametrize("text", ["", "   \n\n", "```\n```"])
def test_empty_messages_are_rejected(text) -> None:
    with pytest.raises(InvalidCommitMessageError, match="Commit message is empty."):
        parse(text)


@pytest.mark.parametrize(
    "text",
    [
        "feat: add greeting",
        "fix(cli)!: handle empty input",
        "docs(readme): explain profiles\n\n- Add a section.\n\nRefs: #12",
    ],
)
def test_to_text_round_trips(text) -> None:
    assert parse(text).to_text() == text
    assert parse(parse(text).to_text()) == parse(text)
