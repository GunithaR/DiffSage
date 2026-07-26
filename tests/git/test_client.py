import subprocess

from pathlib import Path
from datetime import datetime

from diffsage.git.client import GitClient
from diffsage.models.git import GitCommit

from tests.helpers import run_git
from tests.helpers import init_git_repo
from tests.helpers import init_git_repo_with_initial_commit


def test_is_git_repository_returns_false_for_non_git_directory(tmp_path: Path):
    client = GitClient(tmp_path)

    assert client.is_git_repository() is False


def test_is_git_repository_returns_true_for_git_repository(tmp_path: Path):
    init_git_repo(tmp_path)
    client = GitClient(tmp_path)

    assert client.is_git_repository() is True


def test_repository_root_returns_repository_root(tmp_path: Path):
    init_git_repo(tmp_path)
    client = GitClient(tmp_path)

    assert client.repository_root() == tmp_path


def test_current_branch_returns_current_branch(tmp_path: Path):
    init_git_repo(tmp_path)
    client = GitClient(tmp_path)

    assert client.current_branch() == "main"


def test_current_commit_returns_current_commit_hash(tmp_path: Path):
    init_git_repo_with_initial_commit(tmp_path)

    expected = run_git(
        ["rev-parse", "HEAD"],
        tmp_path,
    ).stdout.strip()

    client = GitClient(tmp_path)

    assert client.current_commit() == expected


def test_status_returns_untracked_files(tmp_path: Path):
    init_git_repo(tmp_path)

    readme = tmp_path / "README.md"
    readme.write_text("# DiffSage\n")

    client = GitClient(tmp_path)
    status = client.status()

    assert status.untracked == ["README.md"]


def test_status_returns_modified_files(tmp_path: Path):
    init_git_repo_with_initial_commit(tmp_path)

    readme = tmp_path / "README.md"
    readme.write_text("# DiffSage\n\nModified")

    client = GitClient(tmp_path)
    status = client.status()

    assert status.modified == ["README.md"]


def test_status_returns_added_files(tmp_path: Path):
    init_git_repo(tmp_path)

    readme = tmp_path / "README.md"
    readme.write_text("# DiffSage\n")

    run_git(["add", "README.md"], tmp_path)

    client = GitClient(tmp_path)
    status = client.status()

    assert status.added == ["README.md"]


def test_status_returns_deleted_files(tmp_path: Path):
    init_git_repo_with_initial_commit(tmp_path)

    readme = tmp_path / "README.md"
    readme.unlink()

    client = GitClient(tmp_path)
    status = client.status()

    assert status.deleted == ["README.md"]


def test_staged_diff_returns_git_diff(tmp_path: Path):
    init_git_repo(tmp_path)

    readme = tmp_path / "README.md"
    readme.write_text("# DiffSage\n")

    run_git(["add", "README.md"], tmp_path)

    client = GitClient(tmp_path)
    diff = client.staged_diff()

    assert "diff --git" in diff
    assert "README.md" in diff
    assert "+# DiffSage" in diff


def test_unstaged_diff_returns_git_diff(tmp_path: Path):
    init_git_repo_with_initial_commit(tmp_path)

    readme = tmp_path / "README.md"
    readme.write_text("# DiffSage\n\nModified")

    client = GitClient(tmp_path)
    diff = client.unstaged_diff()

    assert "diff --git" in diff
    assert "README.md" in diff
    assert "+Modified" in diff


def test_recent_commits_return_commit_history(tmp_path: Path):
    init_git_repo(tmp_path)

    readme = tmp_path / "README.md"
    readme.write_text("# DiffSage\n")

    run_git(["add", "README.md"], tmp_path)
    run_git(["commit", "-m", "docs: add README"], tmp_path)

    readme.write_text("# DiffSage\n\nUpdated\n")

    run_git(["add", "README.md"], tmp_path)
    run_git(["commit", "-m", "feat: update README"], tmp_path)

    client = GitClient(tmp_path)
    commits = client.recent_commits(limit=2)

    assert len(commits) == 2

    assert commits[0].message == "feat: update README"
    assert commits[1].message == "docs: add README"

    assert all(isinstance(commit, GitCommit) for commit in commits)

    assert commits[0].author == "Test User"
    assert isinstance(commits[0].date, datetime)
    assert len(commits[0].hash) >= 40


def test_branches_return_local_branches(tmp_path: Path):
    init_git_repo_with_initial_commit(tmp_path)

    run_git(["checkout", "-b", "feature"], tmp_path)

    client = GitClient(tmp_path)
    branches = client.branches()

    assert set(branches) == {"main", "feature"}


def test_tags_return_all_tags(tmp_path: Path):
    init_git_repo_with_initial_commit(tmp_path)

    run_git(["tag", "v0.1.0"], tmp_path)

    run_git(["checkout", "-b", "feature"], tmp_path)
    run_git(["tag", "v0.2.0"], tmp_path)

    client = GitClient(tmp_path)
    tags = client.tags()

    assert set(tags) == {"v0.1.0", "v0.2.0"}
