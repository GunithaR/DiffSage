"""End-to-end tests for how `diffsage pr` chooses and compares against the base branch.

GitHub compares a pull request with the base branch on origin. These tests use a
second clone as a teammate who pushes to origin, so the local copies go out of date.
"""

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from diffsage.cli import app
from tests.helpers import run_git

runner = CliRunner()

DRAFT = json.dumps(
    {
        "title": "Add my feature",
        "summary": "Adds a feature.",
        "why": "Needed.",
        "changes": [],
        "testing": [],
        "risks": [],
        "reviewer_focus": [],
        "breaking_changes": [],
    }
)


def commit_file(repo: Path, name: str) -> None:
    (repo / name).write_text(f"# {name}\n")
    run_git(["add", name], repo)
    run_git(["commit", "-m", f"feat: add {name}"], repo)


@pytest.fixture
def teammate(tmp_path: Path, git_remote: Path) -> Path:
    """A second clone of origin, standing in for someone else pushing to it."""

    clone = tmp_path / "teammate"
    run_git(["clone", str(git_remote), str(clone)], tmp_path)
    run_git(["config", "user.name", "Teammate"], clone)
    run_git(["config", "user.email", "teammate@example.com"], clone)

    return clone


def head_of(repo: Path, ref: str) -> str:
    return run_git(["rev-parse", ref], repo).stdout.strip()


def test_pr_leaves_out_commits_already_on_origin_when_local_main_is_stale(
    git_repo, teammate, fake_provider, fake_gh
) -> None:
    """Regression: the diff was taken against the local main, so a feature branch
    started from an up-to-date origin/main also described the teammate's work."""

    commit_file(teammate, "teammate.py")
    run_git(["push", "origin", "main"], teammate)

    run_git(["fetch", "origin"], git_repo)  # origin/main moves on; local main does not
    run_git(["switch", "-c", "feature/mine", "origin/main"], git_repo)
    commit_file(git_repo, "mine.py")
    run_git(["push", "-u", "origin", "feature/mine"], git_repo)
    fake_provider.queue(DRAFT)

    result = runner.invoke(app, ["pr"], input="n\n")

    assert result.exit_code == 0, result.output
    prompt = fake_provider.prompts[0]
    assert "mine.py" in prompt
    assert "teammate.py" not in prompt
    assert "Base Branch:\nmain" in prompt
    assert fake_gh.calls  # gh was checked, nothing created (answered n)


def test_pr_fetches_the_base_branch_before_comparing(
    git_repo, git_remote, teammate, fake_provider, fake_gh
) -> None:
    """The feature branch already contains the teammate's commit, but origin/main was
    never fetched. Without fetching first, that commit would count as part of the PR."""

    commit_file(teammate, "teammate.py")
    run_git(["push", "origin", "main"], teammate)

    run_git(["switch", "-c", "feature/mine"], git_repo)
    commit_file(git_repo, "mine.py")
    # Merge the teammate's work without updating origin/main (FETCH_HEAD only).
    run_git(["fetch", str(git_remote), "main"], git_repo)
    run_git(["merge", "--no-edit", "FETCH_HEAD"], git_repo)
    run_git(["push", "-u", "origin", "feature/mine"], git_repo)
    stale = head_of(git_repo, "refs/remotes/origin/main")
    fake_provider.queue(DRAFT)

    result = runner.invoke(app, ["pr"], input="n\n")

    assert result.exit_code == 0, result.output
    assert head_of(git_repo, "refs/remotes/origin/main") == head_of(git_remote, "main") != stale
    prompt = fake_provider.prompts[0]
    assert "mine.py" in prompt
    assert "teammate.py" not in prompt
    assert fake_gh.calls


def test_pr_accepts_a_base_branch_that_exists_only_on_origin(
    git_repo, teammate, fake_provider, fake_gh
) -> None:
    """Regression: only local branches were accepted, so `diffsage pr release` failed
    for a base branch that had never been checked out."""

    run_git(["switch", "-c", "release"], teammate)
    commit_file(teammate, "release-notes.md")
    run_git(["push", "origin", "release"], teammate)

    run_git(["switch", "-c", "feature/mine"], git_repo)
    commit_file(git_repo, "mine.py")
    run_git(["push", "-u", "origin", "feature/mine"], git_repo)
    assert run_git(["branch", "--all", "--list", "*release"], git_repo).stdout.strip() == ""
    fake_provider.queue(DRAFT)

    result = runner.invoke(app, ["pr", "release"], input="y\n")

    assert result.exit_code == 0, result.output
    create = next(call for call in fake_gh.calls if call[:2] == ["pr", "create"])
    assert create[2:4] == ["--base", "release"]
    # Compared with origin/release: its own commit is not part of this PR.
    assert "release-notes.md" not in fake_provider.prompts[0]


@pytest.mark.usefixtures("git_remote", "fake_gh")
def test_pr_rejects_a_base_branch_that_is_not_on_origin(git_repo, fake_provider) -> None:
    run_git(["branch", "local-only", "main"], git_repo)
    run_git(["switch", "-c", "feature/mine"], git_repo)
    commit_file(git_repo, "mine.py")
    run_git(["push", "-u", "origin", "feature/mine"], git_repo)

    result = runner.invoke(app, ["pr", "local-only"])

    assert result.exit_code == 1
    assert (
        "✗ Base branch 'local-only' does not exist on origin, so GitHub cannot open a pull "
        "request against it." in " ".join(result.output.split())
    )
    assert fake_provider.prompts == []
