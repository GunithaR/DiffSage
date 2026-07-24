import subprocess

from pathlib import Path

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