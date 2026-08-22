from diffsage.models.pull_request import PullRequestDraft


def test_pull_request_draft_defaults_optional_sections_to_empty_lists() -> None:
    draft = PullRequestDraft(
        title="Add PR generation",
        summary="Adds pull request generation.",
        why="Improve the Git workflow.",
    )

    assert draft.changes == []
    assert draft.testing == []
    assert draft.risks == []
    assert draft.reviewer_focus == []
    assert draft.breaking_changes == []


def test_pull_request_draft_to_dict() -> None:
    draft = PullRequestDraft(
        title="Add pull request generation",
        summary="Adds PR generation.",
        why="Provide structured PR drafts.",
        changes=["Add PR service."],
        testing=["Added unit tests."],
        risks=["AI-generated content requires review."],
        reviewer_focus=["Review service orchestration."],
        breaking_changes=[],
    )

    result = draft.to_dict()

    assert result == {
        "title": "Add pull request generation",
        "summary": "Adds PR generation.",
        "why": "Provide structured PR drafts.",
        "changes": ["Add PR service."],
        "testing": ["Added unit tests."],
        "risks": ["AI-generated content requires review."],
        "reviewer_focus": ["Review service orchestration."],
        "breaking_changes": [],
    }
