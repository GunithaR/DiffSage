from datetime import datetime
from pathlib import Path

from diffsage.git.client import GitClient
from diffsage.models.git import GitCommit
from tests.helpers import init_git_repo, init_git_repo_with_initial_commit, run_git


def test_is_git_repository_returns_false_for_non_git_directory(tmp_path: Path) -> None:
    client = GitClient(tmp_path)

    assert client.is_git_repository() is False


def test_is_git_repository_returns_true_for_git_repository(tmp_path: Path) -> None:
    init_git_repo(tmp_path)
    client = GitClient(tmp_path)

    assert client.is_git_repository() is True


def test_repository_root_returns_repository_root(tmp_path: Path) -> None:
    init_git_repo(tmp_path)
    client = GitClient(tmp_path)

    assert client.repository_root() == tmp_path


def test_current_branch_returns_current_branch(tmp_path: Path) -> None:
    init_git_repo(tmp_path)
    client = GitClient(tmp_path)

    assert client.current_branch() == "main"


def test_current_commit_returns_current_commit_hash(tmp_path: Path) -> None:
    init_git_repo_with_initial_commit(tmp_path)

    expected = run_git(
        ["rev-parse", "HEAD"],
        tmp_path,
    ).stdout.strip()

    client = GitClient(tmp_path)

    assert client.current_commit() == expected


def test_status_returns_untracked_files(tmp_path: Path) -> None:
    init_git_repo(tmp_path)

    readme = tmp_path / "README.md"
    readme.write_text("# DiffSage\n")

    client = GitClient(tmp_path)
    status = client.status()

    assert status.untracked == ["README.md"]


def test_status_returns_modified_files(tmp_path: Path) -> None:
    init_git_repo_with_initial_commit(tmp_path)

    readme = tmp_path / "README.md"
    readme.write_text("# DiffSage\n\nModified")

    client = GitClient(tmp_path)
    status = client.status()

    assert status.modified == ["README.md"]


def test_status_returns_added_files(tmp_path: Path) -> None:
    init_git_repo(tmp_path)

    readme = tmp_path / "README.md"
    readme.write_text("# DiffSage\n")

    run_git(["add", "README.md"], tmp_path)

    client = GitClient(tmp_path)
    status = client.status()

    assert status.added == ["README.md"]


def test_status_returns_deleted_files(tmp_path: Path) -> None:
    init_git_repo_with_initial_commit(tmp_path)

    readme = tmp_path / "README.md"
    readme.unlink()

    client = GitClient(tmp_path)
    status = client.status()

    assert status.deleted == ["README.md"]


def test_staged_diff_returns_git_diff(tmp_path: Path) -> None:
    init_git_repo(tmp_path)

    readme = tmp_path / "README.md"
    readme.write_text("# DiffSage\n")

    run_git(["add", "README.md"], tmp_path)

    client = GitClient(tmp_path)
    diff = client.staged_diff()

    assert "diff --git" in diff
    assert "README.md" in diff
    assert "+# DiffSage" in diff


def test_unstaged_diff_returns_git_diff(tmp_path: Path) -> None:
    init_git_repo_with_initial_commit(tmp_path)

    readme = tmp_path / "README.md"
    readme.write_text("# DiffSage\n\nModified")

    client = GitClient(tmp_path)
    diff = client.unstaged_diff()

    assert "diff --git" in diff
    assert "README.md" in diff
    assert "+Modified" in diff


def test_recent_commits_return_commit_history(tmp_path: Path) -> None:
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


def test_branches_return_local_branches(tmp_path: Path) -> None:
    init_git_repo_with_initial_commit(tmp_path)

    run_git(["checkout", "-b", "feature"], tmp_path)

    client = GitClient(tmp_path)
    branches = client.branches()

    assert set(branches) == {"main", "feature"}


def test_tags_return_all_tags(tmp_path: Path) -> None:
    init_git_repo_with_initial_commit(tmp_path)

    run_git(["tag", "v0.1.0"], tmp_path)

    run_git(["checkout", "-b", "feature"], tmp_path)
    run_git(["tag", "v0.2.0"], tmp_path)

    client = GitClient(tmp_path)
    tags = client.tags()

    assert set(tags) == {"v0.1.0", "v0.2.0"}


def test_merge_base_return_latest_commit_hash(tmp_path: Path) -> None:
    init_git_repo_with_initial_commit(tmp_path)

    (tmp_path / "second.txt").write_text("second commit")
    run_git(["add", "second.txt"], tmp_path)
    run_git(["commit", "-m", "second commit"], tmp_path)
    expected = run_git(["rev-parse", "HEAD"], tmp_path)

    run_git(["checkout", "-b", "feature"], tmp_path)
    (tmp_path / "feature.txt").write_text("feature change")
    run_git(["add", "feature.txt"], tmp_path)
    run_git(["commit", "-m", "third commit from feature"], tmp_path)

    run_git(["checkout", "main"], tmp_path)
    (tmp_path / "main.txt").write_text("main change")
    run_git(["add", "main.txt"], tmp_path)
    run_git(["commit", "-m", "third commit from main"], tmp_path)

    client = GitClient(tmp_path)

    assert client.merge_base("main", "feature") == expected.stdout.strip()


def test_commits_between_return_commit_list(tmp_path: Path) -> None:
    init_git_repo_with_initial_commit(tmp_path)

    run_git(["checkout", "-b", "feature"], tmp_path)

    path = tmp_path / "file.txt"

    path.write_text("feature change")
    run_git(["add", "file.txt"], tmp_path)
    run_git(["commit", "-m", "first commit from feature"], tmp_path)
    feature_commit_1 = run_git(["rev-parse", "HEAD"], tmp_path).stdout.strip()

    path.write_text("feature change again")
    run_git(["add", "file.txt"], tmp_path)
    run_git(["commit", "-m", "second commit from feature"], tmp_path)
    feature_commit_2 = run_git(["rev-parse", "HEAD"], tmp_path).stdout.strip()

    run_git(["checkout", "main"], tmp_path)

    path.write_text("main change")
    run_git(["add", "file.txt"], tmp_path)
    run_git(["commit", "-m", "second commit from main"], tmp_path)

    client = GitClient(tmp_path)
    commits = client.commits_between("main", "feature")

    assert len(commits) == 2

    assert commits[0].hash == feature_commit_2
    assert commits[1].hash == feature_commit_1


def test_changed_files_return_file_list(tmp_path: Path) -> None:
    init_git_repo_with_initial_commit(tmp_path)

    run_git(["checkout","-b","feature"], tmp_path)

    (tmp_path / "feature-file1.txt").write_text("feature 1")
    run_git(["add","feature-file1.txt"], tmp_path)
    run_git(["commit","-m","add feature 1 file"], tmp_path)

    (tmp_path / "feature-file2.txt").write_text("feature 2")
    run_git(["add","feature-file2.txt"], tmp_path)
    run_git(["commit","-m","add feature 2 file"], tmp_path)

    run_git(["checkout","main"], tmp_path)

    (tmp_path / "main.txt").write_text("change from main")
    run_git(["add","main.txt"], tmp_path)
    run_git(["commit","-m","add main file"], tmp_path)

    client = GitClient(tmp_path)

    files = client.changed_files("main", "feature")

    assert set(files) == {
        "feature-file2.txt",
        "feature-file1.txt",
    }


def test_branch_diff_return_changed_context(tmp_path: Path) -> None:
    init_git_repo_with_initial_commit(tmp_path)

    run_git(["checkout","-b","feature"], tmp_path)

    (tmp_path / "feature-file1.txt").write_text("feature 1")
    run_git(["add","feature-file1.txt"], tmp_path)
    run_git(["commit","-m","add feature 1 file"], tmp_path)

    (tmp_path / "feature-file2.txt").write_text("feature 2")
    run_git(["add","feature-file2.txt"], tmp_path)
    run_git(["commit","-m","add feature 2 file"], tmp_path)

    run_git(["checkout","main"], tmp_path)

    (tmp_path / "main.txt").write_text("change from main")
    run_git(["add","main.txt"], tmp_path)
    run_git(["commit","-m","add main file"], tmp_path)

    client = GitClient(tmp_path)

    diff = client.branch_diff("main", "feature")

    assert "feature 1" in diff
    assert "feature 2" in diff
    assert "change from main" not in diff
    assert "feature-file1.txt" in diff
    assert "feature-file2.txt" in diff