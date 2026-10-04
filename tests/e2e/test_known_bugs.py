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
