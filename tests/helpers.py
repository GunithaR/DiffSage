import subprocess
from pathlib import Path

from diffsage.config.defaults import DEFAULT_CONFIG
from diffsage.config.settings import Settings


def run_git(
    args: list[str],
    cwd: Path,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
    )


def init_git_repo(path: Path) -> None:
    """Initialize a Git repository for testing."""

    run_git(
        ["init", "--initial-branch=main"],
        path,
    )

    run_git(
        ["config", "user.name", "Test User"],
        path,
    )

    run_git(
        ["config", "user.email", "test@example.com"],
        path,
    )


def init_git_repo_with_initial_commit(path: Path) -> None:
    """Create a Git repository with one initial commit."""

    init_git_repo(path)

    readme = path / "README.md"
    readme.write_text("# DiffSage\n")

    run_git(["add", "README.md"], path)
    run_git(["commit", "-m", "Initial Commit"], path)


def create_settings(**overrides) -> Settings:
    defaults = {
        "provider": DEFAULT_CONFIG.ai.provider,
        "ai_model": DEFAULT_CONFIG.ai.model,
        "credential_profile": DEFAULT_CONFIG.ai.credential_profile,
        "timeout": DEFAULT_CONFIG.network.timeout,
        "max_retries": DEFAULT_CONFIG.network.max_retries,
        "log_level": DEFAULT_CONFIG.logging.level,
    }

    defaults.update(overrides)
    return Settings(**defaults)


def assert_error_shown(source, message: str | None = None) -> None:
    """Assert the shared command error handler printed an error (optionally this one).

    `source` is pytest's capsys fixture, or the output string of a CliRunner result.
    Whitespace is normalised because Rich may wrap long messages across lines.
    """

    text = source if isinstance(source, str) else source.readouterr().out
    output = " ".join(text.split())

    if message is None:
        assert "✗ " in output, output
    else:
        assert f"✗ {' '.join(message.split())}" in output, output


def install_failing_pre_commit_hook(repo: Path, *lines: str) -> None:
    """A pre-commit hook that prints `lines` and rejects the commit (Git for Windows runs
    hooks through its bundled sh, so this works on every OS)."""

    hook = repo / ".git" / "hooks" / "pre-commit"
    hook.parent.mkdir(parents=True, exist_ok=True)
    echoes = "".join(f"echo '{line}'\n" for line in lines)
    hook.write_text(f"#!/bin/sh\n{echoes}exit 1\n", newline="\n")
    hook.chmod(0o755)
