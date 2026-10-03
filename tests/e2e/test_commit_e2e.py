"""End-to-end tests for `diffsage commit`: real CLI, real Git repository, fake AI provider."""

from pathlib import Path

from typer.testing import CliRunner

from diffsage.cli import app
from tests.helpers import run_git

runner = CliRunner()


def stage_file(repo: Path, name: str, content: str) -> None:
    (repo / name).write_text(content)
    run_git(["add", name], repo)


def head_message(repo: Path) -> str:
    return run_git(["log", "-1", "--format=%B"], repo).stdout.strip()


def commit_count(repo: Path) -> int:
    return int(run_git(["rev-list", "--count", "HEAD"], repo).stdout.strip())


def test_commit_accepts_generated_subject(git_repo, fake_provider) -> None:
    stage_file(git_repo, "greeting.py", "print('hello')\n")
    fake_provider.queue("feat: add greeting script")

    result = runner.invoke(app, ["commit"], input="y\n")

    assert result.exit_code == 0, result.output
    assert "Commit created successfully" in result.output
    assert head_message(git_repo) == "feat: add greeting script"
    assert commit_count(git_repo) == 2


def test_commit_keeps_subject_and_body(git_repo, fake_provider) -> None:
    stage_file(git_repo, "greeting.py", "print('hello')\n")
    fake_provider.queue(
        "feat(cli): add greeting\n\n- Add greeting script.\n- Print a welcome line."
    )

    result = runner.invoke(app, ["commit"], input="\n")

    assert result.exit_code == 0, result.output
    assert head_message(git_repo) == (
        "feat(cli): add greeting\n\n- Add greeting script.\n- Print a welcome line."
    )


def test_commit_prompt_contains_staged_diff(git_repo, fake_provider) -> None:
    stage_file(git_repo, "greeting.py", "print('hello from the staged diff')\n")
    fake_provider.queue("feat: add greeting script")

    runner.invoke(app, ["commit"], input="y\n")

    assert len(fake_provider.prompts) == 1
    assert "hello from the staged diff" in fake_provider.prompts[0]
    assert "Branch:\nmain" in fake_provider.prompts[0]


def test_commit_cancel_creates_no_commit(git_repo, fake_provider) -> None:
    stage_file(git_repo, "greeting.py", "print('hello')\n")
    fake_provider.queue("feat: add greeting script")

    result = runner.invoke(app, ["commit"], input="n\n")

    assert result.exit_code == 0, result.output
    assert "Cancelled" in result.output
    assert commit_count(git_repo) == 1


def test_commit_regenerate_uses_second_message(git_repo, fake_provider) -> None:
    stage_file(git_repo, "greeting.py", "print('hello')\n")
    fake_provider.queue("feat: first attempt", "feat: second attempt")

    result = runner.invoke(app, ["commit"], input="r\ny\n")

    assert result.exit_code == 0, result.output
    assert len(fake_provider.prompts) == 2
    assert head_message(git_repo) == "feat: second attempt"


def test_commit_rejects_invalid_option_then_commits(git_repo, fake_provider) -> None:
    stage_file(git_repo, "greeting.py", "print('hello')\n")
    fake_provider.queue("feat: add greeting script")

    result = runner.invoke(app, ["commit"], input="x\ny\n")

    assert result.exit_code == 0, result.output
    assert "Invalid option" in result.output
    assert commit_count(git_repo) == 2


def test_commit_without_staged_changes_exits_without_calling_ai(git_repo, fake_provider) -> None:
    result = runner.invoke(app, ["commit"])

    assert result.exit_code == 1
    assert "No staged changes found" in result.output
    assert fake_provider.requests == []


def test_commit_outside_git_repository_exits(tmp_path, monkeypatch, fake_provider) -> None:
    outside = tmp_path / "not-a-repo"
    outside.mkdir()
    monkeypatch.chdir(outside)

    result = runner.invoke(app, ["commit"])

    assert result.exit_code == 1
    assert "Not inside a Git repository" in result.output
    assert fake_provider.requests == []


def test_commit_without_credential_exits(git_repo, isolated_env) -> None:
    stage_file(git_repo, "greeting.py", "print('hello')\n")

    result = runner.invoke(app, ["commit"])

    assert result.exit_code == 1
    assert "Credential not found for provider 'gemini'" in result.output
