from pathlib import Path

import pytest

from diffsage.config.paths import find_repository_root, get_local_config_path


def same_path(left: Path | None, right: Path) -> bool:
    """Compare resolved paths: Git reports real paths (e.g. /private/var on macOS)."""

    return left is not None and left.resolve() == right.resolve()


def test_find_repository_root_from_repository_root(git_repo) -> None:
    assert same_path(find_repository_root(), git_repo)


def test_find_repository_root_from_subdirectory(git_repo, monkeypatch) -> None:
    nested = git_repo / "a" / "b"
    nested.mkdir(parents=True)
    monkeypatch.chdir(nested)

    assert same_path(find_repository_root(), git_repo)


@pytest.mark.usefixtures("isolated_env")
def test_find_repository_root_outside_repository_is_none() -> None:
    assert find_repository_root() is None


@pytest.mark.usefixtures("git_repo")
def test_find_repository_root_without_git_installed_is_none(monkeypatch) -> None:
    """Inside a real repository, so only the missing Git can explain the None."""

    monkeypatch.setenv("PATH", "")

    assert find_repository_root() is None


def test_get_local_config_path_points_at_repository_root(git_repo, monkeypatch) -> None:
    nested = git_repo / "docs"
    nested.mkdir()
    monkeypatch.chdir(nested)

    assert same_path(get_local_config_path(), git_repo / ".diffsage.toml")
