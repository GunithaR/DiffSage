"""End-to-end tests for `diffsage pr`: real CLI, real Git repository with an origin
remote, fake AI provider and fake GitHub CLI."""

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from diffsage.cli import app
from tests.helpers import run_git

runner = CliRunner()

DRAFT = {
    "title": "Add greeting script",
    "summary": "Adds a script that prints a greeting.",
    "why": "Gives new users a first command to run.",
    "changes": ["Add greeting.py."],
    "testing": ["Testing status was not provided."],
    "risks": [],
    "reviewer_focus": ["The greeting text."],
    "breaking_changes": [],
}


def draft_json(**changes: object) -> str:
    return json.dumps({**DRAFT, **changes})


def commit_file(repo: Path, name: str, content: str, message: str) -> None:
    (repo / name).write_text(content)
    run_git(["add", name], repo)
    run_git(["commit", "-m", message], repo)


@pytest.fixture
def feature_branch(git_repo: Path, git_remote: Path) -> Path:
    """A pushed feature branch with one commit ahead of main."""

    run_git(["switch", "-c", "feature/greeting"], git_repo)
    commit_file(git_repo, "greeting.py", "print('hello')\n", "feat: add greeting script")
    run_git(["push", "-u", "origin", "feature/greeting"], git_repo)

    return git_repo


def pr_create_call(calls: list[list[str]]) -> list[str] | None:
    return next((call for call in calls if call[:2] == ["pr", "create"]), None)


def test_pr_accept_creates_pull_request(feature_branch, fake_provider, fake_gh) -> None:
    fake_provider.queue(draft_json())

    result = runner.invoke(app, ["pr"], input="y\n")

    assert result.exit_code == 0, result.output
    assert "Pull request created successfully" in result.output
    assert "https://github.com/example/repo/pull/1" in result.output

    call = pr_create_call(fake_gh.calls)
    assert call is not None
    assert call[2:8] == [
        "--base",
        "main",
        "--head",
        "feature/greeting",
        "--title",
        "Add greeting script",
    ]
    assert "## Summary\nAdds a script that prints a greeting." in call[9]


def test_pr_prompt_contains_branch_evidence(feature_branch, fake_provider, fake_gh) -> None:
    fake_provider.queue(draft_json())

    runner.invoke(app, ["pr"], input="n\n")

    prompt = fake_provider.prompts[0]
    assert "Current Branch:\nfeature/greeting" in prompt
    assert "Base Branch:\nmain" in prompt
    assert "greeting.py" in prompt
    assert "feat: add greeting script" in prompt


def test_pr_shows_resolved_branches(feature_branch, fake_provider, fake_gh) -> None:
    fake_provider.queue(draft_json())

    result = runner.invoke(app, ["pr"], input="n\n")

    assert "Head: feature/greeting" in result.output
    assert "Base: main" in result.output


def test_pr_cancel_creates_nothing(feature_branch, fake_provider, fake_gh) -> None:
    fake_provider.queue(draft_json())

    result = runner.invoke(app, ["pr"], input="n\n")

    assert result.exit_code == 0, result.output
    assert "Cancelled" in result.output
    assert pr_create_call(fake_gh.calls) is None


def test_pr_regenerate_uses_second_draft(feature_branch, fake_provider, fake_gh) -> None:
    fake_provider.queue(draft_json(title="First draft"), draft_json(title="Second draft"))

    result = runner.invoke(app, ["pr"], input="r\ny\n")

    assert result.exit_code == 0, result.output
    assert len(fake_provider.prompts) == 2
    assert pr_create_call(fake_gh.calls)[7] == "Second draft"


def test_pr_against_explicit_base_branch(feature_branch, fake_provider, fake_gh) -> None:
    run_git(["branch", "develop", "main"], feature_branch)
    fake_provider.queue(draft_json())

    result = runner.invoke(app, ["pr", "develop"], input="y\n")

    assert result.exit_code == 0, result.output
    assert pr_create_call(fake_gh.calls)[2:4] == ["--base", "develop"]


def test_pr_with_unpushed_commits_exits_before_ai(feature_branch, fake_provider, fake_gh) -> None:
    commit_file(feature_branch, "extra.py", "print('extra')\n", "feat: add extra script")

    result = runner.invoke(app, ["pr"])

    assert result.exit_code == 1
    assert "commits that have not been pushed" in result.output
    assert fake_provider.requests == []


def test_pr_with_unpushed_branch_exits(git_repo, git_remote, fake_provider, fake_gh) -> None:
    run_git(["switch", "-c", "feature/local-only"], git_repo)
    commit_file(git_repo, "local.py", "print('local')\n", "feat: add local script")

    result = runner.invoke(app, ["pr"])

    assert result.exit_code == 1
    assert "Remote branch does not exist on origin" in result.output


def test_pr_on_base_branch_exits(git_repo, git_remote, fake_provider, fake_gh) -> None:
    result = runner.invoke(app, ["pr"])

    assert result.exit_code == 1
    assert "Current branch and base branch are the same" in result.output


def test_pr_unauthenticated_gh_exits_before_ai(feature_branch, fake_provider, fake_gh) -> None:
    fake_gh.configure(authenticated=False)

    result = runner.invoke(app, ["pr"])

    assert result.exit_code == 1
    assert "gh auth login" in result.output
    assert fake_provider.requests == []


def test_pr_without_gh_installed_exits(feature_branch, fake_provider, fake_gh) -> None:
    fake_gh.installed = False

    result = runner.invoke(app, ["pr"])

    assert result.exit_code == 1
    assert "GitHub CLI is not installed" in result.output


def test_pr_invalid_ai_json_exits(feature_branch, fake_provider, fake_gh) -> None:
    fake_provider.queue("This is not JSON")

    result = runner.invoke(app, ["pr"])

    assert result.exit_code == 1
    assert "AI response is not valid JSON" in result.output
    assert pr_create_call(fake_gh.calls) is None
