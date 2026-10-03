"""Known bugs from the v1.3.1 review, pinned as strict expected failures.

Each test describes the CORRECT behaviour. While the bug exists the test fails
and pytest reports it as xfail. When a branch fixes the bug the test passes,
strict mode turns that XPASS into a failure, and the fixing branch must remove
the xfail marker so the test becomes a normal regression test.
"""

import json
from contextlib import contextmanager
from pathlib import Path

import pytest
from typer.testing import CliRunner

from diffsage.cli import app
from diffsage.ui.pull_request_view import PullRequestView
from tests.helpers import run_git

runner = CliRunner()


@pytest.mark.xfail(
    strict=True,
    reason="Bug: `git log` fails in a repo with no commits. Fixed by fix/commit-workflow.",
)
def test_commit_works_for_first_commit_in_empty_repository(empty_git_repo, fake_provider) -> None:
    (empty_git_repo / "README.md").write_text("# New project\n")
    run_git(["add", "README.md"], empty_git_repo)
    fake_provider.queue("chore: initial commit")

    result = runner.invoke(app, ["commit"], input="y\n")

    assert result.exit_code == 0, result.output
    log = run_git(["log", "--format=%s"], empty_git_repo).stdout.strip()
    assert log == "chore: initial commit"


@pytest.fixture
def outside_repository(tmp_path, monkeypatch) -> Path:
    directory = tmp_path / "not-a-repo"
    directory.mkdir()
    monkeypatch.chdir(directory)

    return directory


@pytest.mark.xfail(
    strict=True,
    reason="Bug: --local outside a repository uses a None path. Fixed by fix/configuration.",
)
@pytest.mark.usefixtures("isolated_env", "outside_repository")
def test_config_set_local_outside_repository_explains_the_problem() -> None:
    result = runner.invoke(app, ["config", "set", "model", "some-model", "--local"])

    assert result.exit_code == 1
    assert "unexpected error" not in result.output.lower()
    assert "repository" in result.output.lower()


@pytest.mark.xfail(
    strict=True,
    reason="Bug: config commands print 'Location: None' outside a repository. "
    "Fixed by fix/configuration.",
)
@pytest.mark.usefixtures("isolated_env", "outside_repository")
def test_config_get_outside_repository_does_not_print_none_location() -> None:
    result = runner.invoke(app, ["config", "get", "model"])

    assert result.exit_code == 0, result.output
    assert "None" not in result.output


@pytest.mark.xfail(
    strict=True,
    reason="Bug: repo root is found by checking that .git is a directory, which is a "
    "file in worktrees. Fixed by fix/configuration.",
)
@pytest.mark.usefixtures("isolated_env")
def test_local_config_is_read_inside_git_worktree(git_repo, tmp_path, monkeypatch) -> None:
    worktree = tmp_path / "worktree"
    run_git(["worktree", "add", "-b", "feature/worktree", str(worktree)], git_repo)
    (worktree / ".diffsage.toml").write_text('[ai]\nmodel = "worktree-model"\n')
    monkeypatch.chdir(worktree)

    result = runner.invoke(app, ["config", "get", "model"])

    assert result.exit_code == 0, result.output
    assert "worktree-model" in result.output


class RecordingStatus:
    """Stands in for a Rich status spinner and records every message shown."""

    def __init__(self) -> None:
        self.messages: list[str] = []

    def update(self, message: str) -> None:
        self.messages.append(message)


@pytest.fixture
def recorded_statuses(monkeypatch) -> list[RecordingStatus]:
    """Replace the PR view's spinner; each generating() call adds one recorder."""

    statuses: list[RecordingStatus] = []

    @contextmanager
    def recording_generating(_self):
        status = RecordingStatus()
        statuses.append(status)
        yield status

    monkeypatch.setattr(PullRequestView, "generating", recording_generating)

    return statuses


@pytest.fixture
def pushed_feature_branch(git_repo: Path, git_remote: Path) -> Path:
    run_git(["switch", "-c", "feature/spinner"], git_repo)
    (git_repo / "spinner.py").write_text("print('spin')\n")
    run_git(["add", "spinner.py"], git_repo)
    run_git(["commit", "-m", "feat: add spinner script"], git_repo)
    run_git(["push", "-u", "origin", "feature/spinner"], git_repo)

    assert run_git(["branch", "--list", "feature/spinner"], git_remote).stdout.strip()

    return git_repo


DRAFT = json.dumps(
    {
        "title": "Add spinner script",
        "summary": "Adds a script.",
        "why": "Needed.",
        "changes": [],
        "testing": [],
        "risks": [],
        "reviewer_focus": [],
        "breaking_changes": [],
    }
)


@pytest.mark.usefixtures("pushed_feature_branch", "fake_gh")
def test_pr_first_generation_reports_attempt(fake_provider, recorded_statuses) -> None:
    """Control case for the regenerate bug below: the first spinner works today."""

    fake_provider.queue(DRAFT)

    runner.invoke(app, ["pr"], input="n\n")

    assert recorded_statuses[0].messages == ["Generating pull request draft... Attempt 1/4"]


@pytest.mark.xfail(
    strict=True,
    reason="Bug: regenerate opens a new spinner but updates the closed first one. "
    "Fixed by fix/pr-workflow.",
)
@pytest.mark.usefixtures("pushed_feature_branch", "fake_gh")
def test_pr_regenerate_reports_attempt_on_its_own_spinner(fake_provider, recorded_statuses) -> None:
    fake_provider.queue(DRAFT, DRAFT)

    result = runner.invoke(app, ["pr"], input="r\nn\n")

    assert result.exit_code == 0, result.output
    assert len(recorded_statuses) == 2
    assert recorded_statuses[1].messages == ["Generating pull request draft... Attempt 1/4"]
