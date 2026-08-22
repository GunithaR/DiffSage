from pathlib import Path
from unittest.mock import Mock

import pytest

from diffsage.exceptions import (
    BaseBranchNotFoundError,
    DetachedHeadError,
    RemoteBranchNotFoundError,
    SameBranchError,
    UnpushedChangesError,
)
from diffsage.git.client import GitClient
from diffsage.models.git import CommitContext, PullRequestContext
from diffsage.services.git_service import GitService
from tests.helpers import init_git_repo_with_initial_commit, run_git


def test_build_commit_context_returns_commit_context(tmp_path: Path) -> None:
    init_git_repo_with_initial_commit(tmp_path)

    readme = tmp_path / "README.md"
    readme.write_text("# DiffSage\n\nHello!")

    client = GitClient(tmp_path)
    service = GitService(client)

    context = service.build_commit_context()

    assert isinstance(context, CommitContext)

    assert context.branch == "main"
    assert context.staged_diff == ""
    assert "Hello!" in context.unstaged_diff

    assert len(context.recent_commits) == 1
    assert context.recent_commits[0].message == "Initial Commit"


def test_build_pull_request_context_returns_pull_request_context(tmp_path: Path) -> None:
    init_git_repo_with_initial_commit(tmp_path)

    (tmp_path / "second.txt").write_text("second file")
    run_git(["add", "second.txt"], tmp_path)
    run_git(["commit", "-m", "second commit"], tmp_path)
    expected_merge_base = run_git(
        ["rev-parse", "HEAD"],
        tmp_path,
    ).stdout.strip()

    run_git(["checkout", "-b", "feature"], tmp_path)

    feature_file = tmp_path / "feature.txt"
    feature_file.write_text("feature change")
    run_git(["add", "feature.txt"], tmp_path)
    run_git(["commit", "-m", "feature change"], tmp_path)

    second_feature_file = tmp_path / "second-feature.txt"
    second_feature_file.write_text("second feature change")
    run_git(["add", "second-feature.txt"], tmp_path)
    run_git(["commit", "-m", "second feature change"], tmp_path)

    run_git(["checkout", "main"], tmp_path)

    main_file = tmp_path / "main.txt"
    main_file.write_text("main change")
    run_git(["add", "main.txt"], tmp_path)
    run_git(["commit", "-m", "main change"], tmp_path)

    client = GitClient(tmp_path)
    service = GitService(client)

    run_git(["checkout", "feature"], tmp_path)

    context = service.build_pull_request_context("main")

    assert isinstance(context, PullRequestContext)

    assert context.current_branch == "feature"
    assert context.base_branch == "main"
    assert context.merge_base == expected_merge_base

    assert len(context.commits) == 2
    assert context.commits[0].message == "second feature change"
    assert context.commits[1].message == "feature change"

    assert set(context.changed_files) == {
        "feature.txt",
        "second-feature.txt",
    }

    assert "feature change" in context.diff
    assert "second feature change" in context.diff
    assert "main change" not in context.diff


def test_resolve_base_branch_returns_explicit_branch() -> None:
    client = Mock(spec=GitClient)
    client.current_branch.return_value = "feature"
    client.branches.return_value = ["main", "feature"]

    service = GitService(client)

    assert service.resolve_base_branch("main") == "main"

    client.current_branch.assert_called_once()
    client.branches.assert_called_once()


def test_resolve_base_branch_raises_for_invalid_explicit_branch() -> None:
    client = Mock(spec=GitClient)
    client.current_branch.return_value = "feature"
    client.branches.return_value = ["main", "feature"]

    service = GitService(client)

    with pytest.raises(BaseBranchNotFoundError):
        service.resolve_base_branch("does-not-exist")


def test_resolve_base_branch_uses_git_default_branch() -> None:
    client = Mock(spec=GitClient)

    client.current_branch.return_value = "feature"
    client.default_branch.return_value = "main"
    client.branches.return_value = ["main", "feature"]

    service = GitService(client)

    assert service.resolve_base_branch() == "main"

    client.current_branch.assert_called_once()
    client.default_branch.assert_called_once()


def test_resolve_base_branch_falls_back_to_main() -> None:
    client = Mock(spec=GitClient)

    client.current_branch.return_value = "feature"
    client.default_branch.return_value = None
    client.branches.return_value = ["main", "feature"]

    service = GitService(client)

    assert service.resolve_base_branch() == "main"

    client.current_branch.assert_called_once()
    client.default_branch.assert_called_once()
    client.branches.assert_called_once()


def test_resolve_base_branch_falls_back_to_master() -> None:
    client = Mock(spec=GitClient)

    client.current_branch.return_value = "feature"
    client.default_branch.return_value = None
    client.branches.return_value = ["master", "feature"]

    service = GitService(client)

    assert service.resolve_base_branch() == "master"

    client.current_branch.assert_called_once()
    client.default_branch.assert_called_once()
    client.branches.assert_called_once()


def test_resolve_base_branch_raises_when_no_base_can_be_resolved() -> None:
    client = Mock(spec=GitClient)

    client.current_branch.return_value = "feature"
    client.default_branch.return_value = None
    client.branches.return_value = ["feature"]

    service = GitService(client)

    with pytest.raises(BaseBranchNotFoundError):
        service.resolve_base_branch()

    client.current_branch.assert_called_once()
    client.default_branch.assert_called_once()
    client.branches.assert_called_once()


def test_resolve_base_branch_raises_for_same_branch() -> None:
    client = Mock(spec=GitClient)

    client.current_branch.return_value = "feature"
    client.default_branch.return_value = None
    client.branches.return_value = ["feature"]

    service = GitService(client)

    with pytest.raises(SameBranchError):
        service.resolve_base_branch("feature")


def test_resolve_base_branch_raises_for_detached_head() -> None:
    client = Mock(spec=GitClient)
    client.current_branch.return_value = None

    service = GitService(client)

    with pytest.raises(DetachedHeadError):
        service.resolve_base_branch()

    client.current_branch.assert_called_once()
    client.branches.assert_not_called()
    client.default_branch.assert_not_called()


def test_validate_remote_head_succeeds_when_local_and_remote_match() -> None:
    client = Mock(spec=GitClient)
    client.current_commit.return_value = "abc123"
    client.remote_branch_commit.return_value = "abc123"

    service = GitService(client)

    service.validate_remote_head("feature")

    client.current_commit.assert_called_once()
    client.remote_branch_commit.assert_called_once_with("feature")


def test_validate_remote_head_raises_when_local_branch_has_unpushed_commits() -> None:
    client = Mock(spec=GitClient)
    client.current_commit.return_value = "local123"
    client.remote_branch_commit.return_value = "remote123"

    service = GitService(client)

    with pytest.raises(UnpushedChangesError):
        service.validate_remote_head("feature")

    client.current_commit.assert_called_once()
    client.remote_branch_commit.assert_called_once_with("feature")


def test_validate_remote_head_raises_when_remote_branch_does_not_exist() -> None:
    client = Mock(spec=GitClient)
    client.current_commit.return_value = "local123"
    client.remote_branch_commit.return_value = None

    service = GitService(client)

    with pytest.raises(RemoteBranchNotFoundError):
        service.validate_remote_head("feature")

    client.current_commit.assert_called_once()
    client.remote_branch_commit.assert_called_once_with("feature")
