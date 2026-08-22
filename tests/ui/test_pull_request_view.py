from diffsage.models.pull_request import PullRequestDraft
from diffsage.ui.pull_request_view import PullRequestView


def test_show_branches(capsys) -> None:
    view = PullRequestView()

    view.show_branches(
        base_branch="main",
        head_branch="feature/pr-generation",
    )

    output = capsys.readouterr().out

    assert "main" in output
    assert "feature/pr-generation" in output


def test_show_generated_displays_pull_request_draft(capsys) -> None:
    draft = PullRequestDraft(
        title="Add pull request generation",
        summary="Adds structured pull request generation.",
        why="Provides developers with generated PR drafts.",
        changes=[
            "Add pull request orchestration.",
            "Add deterministic PR analysis.",
        ],
        testing=[
            "Run unit tests.",
            "Run full test suite.",
        ],
        risks=[
            "Changes affect the public CLI.",
        ],
        reviewer_focus=[
            "Review command behavior.",
            "Review generated PR content.",
        ],
        breaking_changes=[],
    )

    view = PullRequestView()
    view.show_generated(draft)

    output = capsys.readouterr().out

    assert draft.title in output
    assert draft.summary in output
    assert draft.why in output

    for change in draft.changes:
        assert change in output

    for test in draft.testing:
        assert test in output

    for risk in draft.risks:
        assert risk in output

    for focus in draft.reviewer_focus:
        assert focus in output

    for breaking_change in draft.breaking_changes:
        assert breaking_change in output


def test_show_generated_displays_none_for_empty_sections(capsys) -> None:
    draft = PullRequestDraft(
        title="Documentation update",
        summary="Updates documentation.",
        why="Improves project documentation.",
    )

    view = PullRequestView()
    view.show_generated(draft)

    output = capsys.readouterr().out

    assert draft.title in output
    assert draft.summary in output
    assert draft.why in output

    assert output.count("None") >= 5


def test_show_not_git_repository(capsys) -> None:
    view = PullRequestView()

    view.show_not_git_repository()

    assert "Not inside a Git repository" in capsys.readouterr().out


def test_show_detached_head(capsys) -> None:
    view = PullRequestView()

    view.show_detached_head()

    assert "detached HEAD" in capsys.readouterr().out


def test_show_base_branch_not_found(capsys) -> None:
    view = PullRequestView()

    view.show_base_branch_not_found()

    assert "base branch" in capsys.readouterr().out


def test_show_same_branch(capsys) -> None:
    view = PullRequestView()

    view.show_same_branch()

    assert "same" in capsys.readouterr().out


def test_prompt_action_returns_user_choice(monkeypatch) -> None:
    view = PullRequestView()

    monkeypatch.setattr(
        view._console,
        "input",
        lambda _: "e",
    )

    assert view.prompt_action() == "e"


def test_show_cancelled(capsys) -> None:
    view = PullRequestView()

    view.show_cancelled()

    assert "Cancelled" in capsys.readouterr().out


def test_show_invalid_option(capsys) -> None:
    view = PullRequestView()

    view.show_invalid_option()

    output = capsys.readouterr().out

    assert "Invalid option" in output
