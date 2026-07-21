import subprocess

from pathlib import Path

from diffsage.git.client import GitClient

def test_is_git_repository_returns_false_for_non_git_directory(tmp_path: Path):
    client = GitClient(tmp_path)

    assert client.is_git_repository() is False


def test_is_git_repository_returns_true_for_git_repository(tmp_path: Path):
    subprocess.run(
        ["git", "init"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
    )
    client = GitClient(tmp_path)

    assert client.is_git_repository() is True


def test_repository_root_returns_repository_root(tmp_path: Path):
    subprocess.run(
        ["git", "init"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
    )

    client = GitClient(tmp_path)

    assert client.repository_root() == tmp_path