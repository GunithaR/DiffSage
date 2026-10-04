"""End-to-end tests for `diffsage commit`: real CLI, real Git repository, fake AI provider."""

import json
import sys
from pathlib import Path

import pytest
from typer.testing import CliRunner

from diffsage.cli import app
from diffsage.commands.error_handler import UNEXPECTED_ERROR_MESSAGE
from tests.helpers import install_failing_pre_commit_hook, run_git

runner = CliRunner()


def flat(output: str) -> str:
    """Join lines, because Rich wraps long messages."""

    return " ".join(output.split())


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


@pytest.mark.usefixtures("git_repo")
def test_commit_without_staged_changes_exits_without_calling_ai(fake_provider) -> None:
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


@pytest.mark.usefixtures("isolated_env")
def test_commit_without_credential_exits(git_repo) -> None:
    stage_file(git_repo, "greeting.py", "print('hello')\n")

    result = runner.invoke(app, ["commit"])

    assert result.exit_code == 1
    assert "Credential not found for provider 'gemini'" in result.output


def test_commit_reports_unparseable_ai_message(git_repo, fake_provider) -> None:
    """Regression: an AI reply without '<type>: <subject>' was reported as unexpected."""

    stage_file(git_repo, "greeting.py", "print('hello')\n")
    fake_provider.queue("Here is a summary of your change")

    result = runner.invoke(app, ["commit"])

    assert result.exit_code == 1
    assert "✗ The first line must look like '<type>[(scope)][!]: <subject>'" in result.output
    assert "Got: 'Here is a summary of your change'" in result.output
    assert UNEXPECTED_ERROR_MESSAGE not in result.output
    assert commit_count(git_repo) == 1


def test_commit_reports_missing_editor(git_repo, fake_provider, monkeypatch) -> None:
    """Regression: a missing editor raised RuntimeError, reported as unexpected."""

    monkeypatch.setenv("VISUAL", "diffsage-missing-editor")
    stage_file(git_repo, "greeting.py", "print('hello')\n")
    fake_provider.queue("feat: add greeting script")

    result = runner.invoke(app, ["commit"], input="e\n")

    assert result.exit_code == 1
    assert '✗ Unable to launch "diffsage-missing-editor".' in result.output
    assert UNEXPECTED_ERROR_MESSAGE not in result.output
    assert commit_count(git_repo) == 1


GOOGLE_KEY = "AIzaSyA1234567890abcdefghijklmnopqrstuv"


def test_commit_never_sends_secrets_to_the_ai(git_repo, fake_provider) -> None:
    stage_file(git_repo, "settings.py", f'GEMINI_KEY = "{GOOGLE_KEY}"\n')
    stage_file(git_repo, ".env", "STRIPE_SECRET=sk_live_abcdefgh\n")
    stage_file(git_repo, "package-lock.json", '{"lockfileVersion": 3}\n')
    fake_provider.queue("chore: add settings")

    result = runner.invoke(app, ["commit"], input="y\n")

    assert result.exit_code == 0, result.output
    prompt = fake_provider.prompts[0]
    assert GOOGLE_KEY not in prompt
    assert "sk_live_abcdefgh" not in prompt
    assert "lockfileVersion" not in prompt
    assert "Diff Notes:" in prompt
    assert "! 1 value(s) that looked like secrets were replaced with [REDACTED]." in result.output
    assert "! Contents of files that may hold secrets were not sent: .env" in result.output
    assert "! Lockfile contents were not sent: package-lock.json" in result.output


def test_commit_with_a_clean_diff_has_no_notes_or_warnings(git_repo, fake_provider) -> None:
    stage_file(git_repo, "greeting.py", "print('hello')\n")
    fake_provider.queue("feat: add greeting script")

    result = runner.invoke(app, ["commit"], input="y\n")

    assert result.exit_code == 0, result.output
    assert "Diff Notes:" not in fake_provider.prompts[0]
    assert "!" not in result.output


def test_commit_works_for_first_commit_in_empty_repository(empty_git_repo, fake_provider) -> None:
    """Regression: `git log` fails in a repository with no commits, which crashed commit."""

    stage_file(empty_git_repo, "README.md", "# New project\n")
    fake_provider.queue("chore: initial commit")

    result = runner.invoke(app, ["commit"], input="y\n")

    assert result.exit_code == 0, result.output
    assert head_message(empty_git_repo) == "chore: initial commit"
    assert "Recent Commits:" in fake_provider.prompts[0]


def test_commit_strips_code_fences_and_preamble_from_the_ai_reply(git_repo, fake_provider) -> None:
    """Regression: fenced replies were rejected; once accepted, the raw text (fences and
    all) would have been committed."""

    stage_file(git_repo, "banner.py", "print('banner')\n")
    fake_provider.queue(
        "Here is a commit message for your changes:\n\n```text\nfeat(ui): add banner\n\n"
        "- Add banner script.\n```\n"
    )

    result = runner.invoke(app, ["commit"], input="y\n")

    assert result.exit_code == 0, result.output
    assert head_message(git_repo) == "feat(ui): add banner\n\n- Add banner script."


def test_commit_keeps_the_breaking_change_marker(git_repo, fake_provider) -> None:
    stage_file(git_repo, "api.py", "def v2(): ...\n")
    fake_provider.queue("feat(api)!: drop v1 endpoints\n\nBREAKING CHANGE: v1 is removed.")

    result = runner.invoke(app, ["commit"], input="y\n")

    assert result.exit_code == 0, result.output
    assert "Breaking" in result.output
    assert (
        head_message(git_repo) == "feat(api)!: drop v1 endpoints\n\nBREAKING CHANGE: v1 is removed."
    )


def test_edit_starts_from_the_cleaned_message(
    git_repo, fake_provider, tmp_path, monkeypatch
) -> None:
    seen = tmp_path / "seen.txt"
    editor = tmp_path / "editor.py"
    editor.write_text(f"import shutil, sys\nshutil.copy(sys.argv[1], {str(seen)!r})\n")
    python = sys.executable.replace("\\", "/")
    monkeypatch.setenv("VISUAL", f'"{python}" "{editor.as_posix()}"')
    stage_file(git_repo, "banner.py", "print('banner')\n")
    fake_provider.queue("```\nfeat(ui): add banner\n```")

    result = runner.invoke(app, ["commit"], input="e\ny\n")

    assert result.exit_code == 0, result.output
    assert seen.read_text() == "feat(ui): add banner"
    assert head_message(git_repo) == "feat(ui): add banner"


def test_commit_rejected_by_a_hook_shows_why(git_repo, fake_provider) -> None:
    stage_file(git_repo, "app.py", "x = 1  \n")
    install_failing_pre_commit_hook(git_repo, "lint: trailing whitespace in app.py line 1")
    fake_provider.queue("feat: add app")

    result = runner.invoke(app, ["commit"], input="y\n")

    assert result.exit_code == 1
    assert "✗ git commit failed. Nothing was committed" in result.output
    assert "lint: trailing whitespace in app.py line 1" in result.output
    assert UNEXPECTED_ERROR_MESSAGE not in result.output
    assert commit_count(git_repo) == 1


def scripted_editor(tmp_path: Path, monkeypatch, outputs: list[str]) -> Path:
    """Set VISUAL to an editor that writes outputs[n] on its n-th run and saves what it was
    opened with to received/<n>.txt."""

    received = tmp_path / "received"
    received.mkdir()
    script = tmp_path / "editor.py"
    script.write_text(
        "import json, shutil, sys\n"
        "from pathlib import Path\n"
        f"received = Path({str(received)!r})\n"
        "run = len(list(received.iterdir()))\n"
        "shutil.copy(sys.argv[1], received / f'{run}.txt')\n"
        f"outputs = json.loads({json.dumps(json.dumps(outputs))})\n"
        "Path(sys.argv[1]).write_text(outputs[run], encoding='utf-8')\n"
    )
    python = sys.executable.replace("\\", "/")
    monkeypatch.setenv("VISUAL", f'"{python}" "{script.as_posix()}"')
    return received


def test_invalid_edit_is_kept_and_reopened(git_repo, fake_provider, tmp_path, monkeypatch) -> None:
    """Regression: an edit that did not parse ended the command and was lost."""

    received = scripted_editor(tmp_path, monkeypatch, ["wip: half done", "feat: done properly"])
    stage_file(git_repo, "app.py", "x = 1\n")
    fake_provider.queue("feat: add app")

    result = runner.invoke(app, ["commit"], input="e\ne\ny\n")

    assert result.exit_code == 0, result.output
    assert "✗ 'wip' is not a Conventional Commit type" in result.output
    assert "! Your edit was kept. Press E to continue editing it." in flat(result.output)
    assert (received / "0.txt").read_text() == "feat: add app"
    assert (received / "1.txt").read_text() == "wip: half done"
    assert head_message(git_repo) == "feat: done properly"
    assert len(fake_provider.prompts) == 1


def test_y_after_an_invalid_edit_commits_the_unchanged_message(
    git_repo, fake_provider, tmp_path, monkeypatch
) -> None:
    scripted_editor(tmp_path, monkeypatch, ["not a commit message"])
    stage_file(git_repo, "app.py", "x = 1\n")
    fake_provider.queue("feat: add app")

    result = runner.invoke(app, ["commit"], input="e\ny\n")

    assert result.exit_code == 0, result.output
    assert head_message(git_repo) == "feat: add app"


def test_unusable_regeneration_keeps_the_previous_message(git_repo, fake_provider) -> None:
    """Regression: an unparseable reply on regenerate ended the command."""

    stage_file(git_repo, "app.py", "x = 1\n")
    fake_provider.queue("feat: add app", "Sorry, I cannot help with that.")

    result = runner.invoke(app, ["commit"], input="r\ny\n")

    assert result.exit_code == 0, result.output
    assert "! The new suggestion could not be used." in flat(result.output)
    assert head_message(git_repo) == "feat: add app"


def test_valid_edit_clears_the_kept_edit(git_repo, fake_provider, tmp_path, monkeypatch) -> None:
    received = scripted_editor(tmp_path, monkeypatch, ["wip: x", "fix: first fix", "fix: second"])
    stage_file(git_repo, "app.py", "x = 1\n")
    fake_provider.queue("feat: add app")

    result = runner.invoke(app, ["commit"], input="e\ne\ne\ny\n")

    assert result.exit_code == 0, result.output
    assert (received / "2.txt").read_text() == "fix: first fix"
    assert head_message(git_repo) == "fix: second"


def test_only_staged_changes_are_sent_to_the_ai(git_repo, fake_provider) -> None:
    """Regression: unstaged work was sent too, so messages described changes that were not
    being committed, and code left out of the commit still reached the provider."""

    stage_file(git_repo, "feature.py", "print('staged feature')\n")
    (git_repo / "README.md").write_text("# DiffSage\n\nunstaged draft notes\n")
    (git_repo / "scratch.py").write_text("print('untracked experiment')\n")
    fake_provider.queue("feat: add feature")

    result = runner.invoke(app, ["commit"], input="y\n")

    assert result.exit_code == 0, result.output
    prompt = fake_provider.prompts[0]
    assert "staged feature" in prompt
    assert "unstaged draft notes" not in prompt
    assert "untracked experiment" not in prompt
    assert "Unstaged" not in prompt
