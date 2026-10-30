"""End-to-end tests for running `commit` and `pr` where nobody can answer a prompt:
CI jobs, git hooks and pipes."""

import os
import subprocess
import sys
from pathlib import Path

import pytest
from typer.testing import CliRunner

from diffsage.cli import app
from tests.helpers import run_git

runner = CliRunner()


def flat(output: str) -> str:
    return " ".join(output.split())


@pytest.fixture
def no_terminal(monkeypatch) -> None:
    monkeypatch.setattr("diffsage.commands.options.stdin_is_terminal", lambda: False)


def stage_file(repo: Path) -> None:
    (repo / "greeting.py").write_text("print('hello')\n")
    run_git(["add", "greeting.py"], repo)


def commit_count(repo: Path) -> int:
    return int(run_git(["rev-list", "--count", "HEAD"], repo).stdout.strip())


@pytest.mark.usefixtures("no_terminal")
def test_commit_without_a_terminal_stops_before_the_ai(git_repo, fake_provider) -> None:
    """Regression: the AI was called, then reading the answer failed with "An unexpected
    error occurred" (or, on an open pipe, the command waited forever)."""

    stage_file(git_repo)

    result = runner.invoke(app, ["commit"])

    assert result.exit_code == 2
    assert (
        "✗ diffsage commit needs a terminal to ask before committing. In scripts and CI, add "
        "--yes to go ahead without asking, or --dry-run to only show the result."
        in flat(result.output)
    )
    assert fake_provider.requests == []
    assert commit_count(git_repo) == 1


@pytest.mark.usefixtures("no_terminal", "git_remote")
def test_pr_without_a_terminal_stops_before_any_network_call(
    git_repo, fake_provider, fake_gh
) -> None:
    run_git(["switch", "-c", "feature/x"], git_repo)

    result = runner.invoke(app, ["pr"])

    assert result.exit_code == 2
    assert "diffsage pr needs a terminal to ask before creating the pull request" in flat(
        result.output
    )
    assert fake_provider.requests == []
    assert fake_gh.calls == []


@pytest.mark.usefixtures("no_terminal")
@pytest.mark.parametrize(("flag", "commits"), [("--yes", 2), ("--dry-run", 1)])
def test_commit_without_a_terminal_works_with_yes_or_dry_run(
    git_repo, fake_provider, flag, commits
) -> None:
    stage_file(git_repo)
    fake_provider.queue("feat: add greeting script")

    result = runner.invoke(app, ["commit", flag])

    assert result.exit_code == 0, result.output
    assert commit_count(git_repo) == commits


def run_diffsage_process(tmp_path: Path, *args: str, **env: str) -> subprocess.CompletedProcess:
    """Run DiffSage as its own process with stdin from /dev/null, exactly like a CI job.

    The terminal check comes before configuration, credentials and git, so an empty
    home folder is enough.
    """

    home = str(tmp_path)

    return subprocess.run(
        [sys.executable, "-c", "from diffsage.cli import app; app()", *args],
        cwd=tmp_path,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env={
            **os.environ,
            "HOME": home,
            "USERPROFILE": home,
            "APPDATA": home,
            "LOCALAPPDATA": home,
            "COLUMNS": "200",
            **env,
        },
    )


def test_a_real_process_with_stdin_from_dev_null_is_not_a_terminal(tmp_path) -> None:
    result = run_diffsage_process(tmp_path, "commit")

    assert result.returncode == 2, result.stdout + result.stderr
    assert "needs a terminal to ask before committing" in flat(result.stdout + result.stderr)


def test_errors_print_where_the_output_is_not_utf8(tmp_path) -> None:
    """Regression: with an ASCII-only output (some CI and Docker images), printing the ✗
    of any error raised UnicodeEncodeError, so the message became a traceback."""

    result = run_diffsage_process(tmp_path, "commit", PYTHONIOENCODING="ascii")

    output = result.stdout + result.stderr
    assert result.returncode == 2, output
    assert "UnicodeEncodeError" not in output
    assert "? diffsage commit needs a terminal to ask before committing" in flat(output)
