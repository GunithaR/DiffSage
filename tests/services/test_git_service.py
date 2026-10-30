from pathlib import Path
from unittest.mock import Mock

import pytest

from diffsage.exceptions import (
    BaseBranchNotFoundError,
    BranchesDivergedError,
    DetachedHeadError,
    FetchFailedError,
    RemoteAheadError,
    RemoteBranchNotFoundError,
    RemoteUnavailableError,
    SameBranchError,
    UnpushedChangesError,
)
from diffsage.git.client import GitClient
from diffsage.models.git import CommitContext, PullRequestContext
from diffsage.services.git_service import GitService
from tests.helpers import init_git_repo_with_initial_commit, run_git


def test_build_commit_context_contains_only_staged_changes(tmp_path: Path) -> None:
    """Regression: unstaged changes were sent too, although they are not part of the commit."""

    init_git_repo_with_initial_commit(tmp_path)
    (tmp_path / "staged.py").write_text("print('staged')\n")
    run_git(["add", "staged.py"], tmp_path)
    (tmp_path / "README.md").write_text("# DiffSage\n\nUnstaged edit!")

    client = GitClient(tmp_path)
    service = GitService(client)

    context = service.build_commit_context()

    assert isinstance(context, CommitContext)

    assert context.branch == "main"
    assert "print('staged')" in context.staged_diff
    assert "Unstaged edit!" not in context.staged_diff
    assert not hasattr(context, "unstaged_diff")

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

    client.ref_exists.return_value = False
    client.remote_has_branch.return_value = False

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

    client.ref_exists.return_value = False
    client.remote_has_branch.return_value = False

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

    client.ref_exists.return_value = False
    client.remote_has_branch.return_value = False

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
    client.is_ancestor.return_value = True

    service = GitService(client)

    with pytest.raises(UnpushedChangesError):
        service.validate_remote_head("feature")

    client.current_commit.assert_called_once()
    client.remote_branch_commit.assert_called_once_with("feature")


def test_validate_remote_head_raises_when_remote_branch_does_not_exist() -> None:
    client = Mock(spec=GitClient)
    client.current_commit.return_value = "local123"
    client.remote_branch_commit.return_value = None
    client.remote_has_branch.return_value = False

    service = GitService(client)

    with pytest.raises(RemoteBranchNotFoundError):
        service.validate_remote_head("feature")

    client.current_commit.assert_called_once()
    client.remote_branch_commit.assert_called_once_with("feature")


def comparison_client(*, on_origin, fetch_error=None, tracking=False, local=("main",)) -> Mock:
    client = Mock(spec=GitClient)
    client.remote_has_branch.return_value = on_origin
    client.fetch_branch.side_effect = fetch_error
    client.ref_exists.return_value = tracking
    client.branches.return_value = list(local)
    return client


def test_base_comparison_ref_fetches_and_uses_origin() -> None:
    client = comparison_client(on_origin=True)
    notices: list[str] = []

    ref = GitService(client).base_comparison_ref("main", on_notice=notices.append)

    assert ref == "refs/remotes/origin/main"
    client.fetch_branch.assert_called_once_with("main")
    assert notices == []


def test_base_comparison_ref_rejects_a_base_that_origin_does_not_have() -> None:
    client = comparison_client(on_origin=False)

    with pytest.raises(BaseBranchNotFoundError, match="does not exist on origin"):
        GitService(client).base_comparison_ref("main")

    client.fetch_branch.assert_not_called()


def test_base_comparison_ref_falls_back_to_last_fetched_origin_when_fetch_fails() -> None:
    client = comparison_client(
        on_origin=True, fetch_error=FetchFailedError("could not read from remote"), tracking=True
    )
    notices: list[str] = []

    ref = GitService(client).base_comparison_ref("main", on_notice=notices.append)

    assert ref == "refs/remotes/origin/main"
    assert notices == [
        "Could not update origin/main (could not read from remote). Comparing against "
        "origin/main as last fetched, which may be out of date."
    ]


def test_base_comparison_ref_falls_back_to_the_local_branch_when_origin_is_unreachable() -> None:
    client = comparison_client(on_origin=None)
    notices: list[str] = []

    ref = GitService(client).base_comparison_ref("main", on_notice=notices.append)

    assert ref == "main"
    assert notices == [
        "Could not fetch main from origin (origin could not be reached). Comparing against "
        "your local main, which may be out of date."
    ]
    client.fetch_branch.assert_not_called()


def test_base_comparison_ref_fails_when_nothing_can_be_compared() -> None:
    client = comparison_client(on_origin=None, local=())

    with pytest.raises(BaseBranchNotFoundError, match="Could not fetch base branch 'main'"):
        GitService(client).base_comparison_ref("main")


def test_resolve_base_branch_accepts_a_branch_only_on_origin() -> None:
    client = Mock(spec=GitClient)
    client.current_branch.return_value = "feature"
    client.branches.return_value = ["main", "feature"]
    client.ref_exists.return_value = False
    client.remote_has_branch.return_value = True

    assert GitService(client).resolve_base_branch("release") == "release"

    client.remote_has_branch.assert_called_once_with("release")


def test_build_pull_request_context_compares_against_the_given_ref() -> None:
    client = Mock(spec=GitClient)
    client.current_branch.return_value = "feature"
    client.merge_base.return_value = "abc"
    client.commits_between.return_value = []
    client.changed_files.return_value = []
    client.branch_diff.return_value = ""

    context = GitService(client).build_pull_request_context("main", "refs/remotes/origin/main")

    assert context.base_branch == "main"
    client.merge_base.assert_called_once_with("refs/remotes/origin/main", "feature")
    client.branch_diff.assert_called_once_with("refs/remotes/origin/main", "feature")


def sync_client(*, remote_in_local, local_in_remote, remote_known=True) -> Mock:
    client = Mock(spec=GitClient)
    client.current_commit.return_value = "local"
    client.remote_branch_commit.return_value = "remote"
    client.ref_exists.return_value = remote_known
    client.is_ancestor.side_effect = lambda ancestor, _descendant: (
        remote_in_local if ancestor == "remote" else local_in_remote
    )
    return client


def test_validate_remote_head_reports_a_branch_behind_origin() -> None:
    client = sync_client(remote_in_local=False, local_in_remote=True)

    with pytest.raises(RemoteAheadError, match="git pull"):
        GitService(client).validate_remote_head("feature")

    client.fetch_branch.assert_not_called()


def test_validate_remote_head_reports_diverged_branches() -> None:
    client = sync_client(remote_in_local=False, local_in_remote=False)

    with pytest.raises(BranchesDivergedError, match="have diverged"):
        GitService(client).validate_remote_head("feature")


def test_validate_remote_head_fetches_an_unknown_origin_commit_before_deciding() -> None:
    client = sync_client(remote_in_local=None, local_in_remote=False, remote_known=False)

    with pytest.raises(BranchesDivergedError):
        GitService(client).validate_remote_head("feature")

    client.fetch_branch.assert_called_once_with("feature")


def test_validate_remote_head_says_pull_when_origin_commit_cannot_be_fetched() -> None:
    client = sync_client(remote_in_local=None, local_in_remote=None, remote_known=False)
    client.fetch_branch.side_effect = FetchFailedError("offline")

    with pytest.raises(RemoteAheadError):
        GitService(client).validate_remote_head("feature")


def test_validate_remote_head_reports_an_unreachable_origin() -> None:
    client = Mock(spec=GitClient)
    client.current_commit.return_value = "local"
    client.remote_branch_commit.return_value = None
    client.remote_has_branch.return_value = None

    with pytest.raises(RemoteUnavailableError, match="Could not reach origin"):
        GitService(client).validate_remote_head("feature")
