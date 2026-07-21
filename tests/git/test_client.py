import subprocess

from pathlib import Path

from diffsage.git.client import GitClient


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


def test_is_git_repository_returns_false_for_non_git_directory(tmp_path: Path):
    client = GitClient(tmp_path)

    assert client.is_git_repository() is False


def test_is_git_repository_returns_true_for_git_repository(tmp_path: Path):
    run_git(
        ["init"],
        tmp_path,
    )
    client = GitClient(tmp_path)

    assert client.is_git_repository() is True


def test_repository_root_returns_repository_root(tmp_path: Path):
    run_git(
        ["init"],
        tmp_path,
    )
    client = GitClient(tmp_path)

    assert client.repository_root() == tmp_path


def test_current_branch_returns_current_branch(tmp_path: Path):
    run_git(
        ["init", "--initial-branch=main"],
        tmp_path
    )
    client = GitClient(tmp_path)

    assert client.current_branch() == "main"


def test_current_commit_returns_current_commit_hash(tmp_path: Path):
    run_git(
        ["init", "--initial-branch=main"],
        tmp_path,
    )

    run_git(
    ["config", "user.name", "Test User"],
    tmp_path,
    )

    run_git(
        ["config", "user.email", "test@example.com"],
        tmp_path,
    )

    readme = tmp_path / "README.md"
    readme.write_text("# DiffSage\n")

    run_git(
        ["add", "README.md"],
        tmp_path,
    )

    run_git(
        ["commit", "-m", "Initial Commit"],
        tmp_path,
    )

    expected = run_git(
        ["rev-parse", "HEAD"],
        tmp_path,
    ).stdout.strip()

    client = GitClient(tmp_path)

    assert client.current_commit() == expected

