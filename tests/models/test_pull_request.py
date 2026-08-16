from diffsage.models.pull_request import PullRequestDraft


def test_pull_request_draft_defaults_optional_sections_to_empty_lists():
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
