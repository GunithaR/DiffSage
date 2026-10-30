"""End-to-end tests for the check that the PR branch matches its copy on origin.

When they differ, the message must say which side is behind, because the fix
differs: push, pull, or pull and then push.
"""

from pathlib import Path

import pytest
from typer.testing import CliRunner

from diffsage.cli import app
from diffsage.exit_codes import ExitCode
from tests.helpers import run_git

runner = CliRunner()


def commit_file(repo: Path, name: str) -> None:
    (repo / name).write_text(f"# {name}\n")
    run_git(["add", name], repo)
    run_git(["commit", "-m", f"feat: add {name}"], repo)


def flat(output: str) -> str:
    return " ".join(output.split())


@pytest.fixture
def pushed_feature(git_repo: Path, git_remote: Path, tmp_path: Path) -> Path:
    """feature/mine pushed to origin, plus a second clone of it at tmp_path/elsewhere
    (the same branch checked out on another machine, or a teammate)."""

    run_git(["switch", "-c", "feature/mine"], git_repo)
    commit_file(git_repo, "mine.py")
    run_git(["push", "-u", "origin", "feature/mine"], git_repo)

    elsewhere = tmp_path / "elsewhere"
    run_git(["clone", "--branch", "feature/mine", str(git_remote), str(elsewhere)], tmp_path)
    run_git(["config", "user.name", "Elsewhere"], elsewhere)
    run_git(["config", "user.email", "elsewhere@example.com"], elsewhere)

    return git_repo


@pytest.mark.usefixtures("fake_gh")
def test_pr_says_to_push_when_local_commits_are_not_on_origin(
    pushed_feature, fake_provider
) -> None:
    commit_file(pushed_feature, "unpushed.py")

    result = runner.invoke(app, ["pr"])

    assert result.exit_code == ExitCode.GIT
    assert (
        "✗ Local branch 'feature/mine' has commits that have not been pushed to origin. "
        "Push them first: git push" in flat(result.output)
    )
    assert fake_provider.requests == []


@pytest.mark.usefixtures("pushed_feature", "fake_gh")
def test_pr_says_to_pull_when_origin_has_commits_the_local_branch_lacks(
    tmp_path, fake_provider
) -> None:
    """Regression: this was reported as "commits that have not been pushed", and the
    suggested push would have been rejected."""

    elsewhere = tmp_path / "elsewhere"
    commit_file(elsewhere, "from-elsewhere.py")
    run_git(["push"], elsewhere)

    result = runner.invoke(app, ["pr"])

    assert result.exit_code == ExitCode.GIT
    assert (
        "✗ origin/feature/mine has commits that your local branch does not have. Pull them "
        "first: git pull" in flat(result.output)
    )
    assert "not been pushed" not in result.output
    assert fake_provider.requests == []


@pytest.mark.usefixtures("fake_gh")
def test_pr_says_to_combine_when_the_branches_have_diverged(
    pushed_feature, tmp_path, fake_provider
) -> None:
    elsewhere = tmp_path / "elsewhere"
    commit_file(elsewhere, "from-elsewhere.py")
    run_git(["push"], elsewhere)
    commit_file(pushed_feature, "unpushed.py")

    result = runner.invoke(app, ["pr"])

    assert result.exit_code == ExitCode.GIT
    assert (
        "✗ Local branch 'feature/mine' and origin/feature/mine have diverged: each has "
        "commits the other does not." in flat(result.output)
    )
    assert "git pull --rebase" in flat(result.output)
    assert fake_provider.requests == []


@pytest.mark.usefixtures("fake_gh", "fake_provider")
def test_pr_says_origin_is_unreachable_instead_of_branch_missing(pushed_feature, tmp_path) -> None:
    """Regression: an unreachable origin was reported as the branch not existing."""

    run_git(["remote", "set-url", "origin", str(tmp_path / "gone.git")], pushed_feature)

    result = runner.invoke(app, ["pr", "main"])

    assert result.exit_code == ExitCode.GIT
    assert "✗ Could not reach origin to check branch 'feature/mine'." in flat(result.output)
    assert "does not exist" not in result.output
