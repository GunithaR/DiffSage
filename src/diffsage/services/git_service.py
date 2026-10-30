from collections.abc import Callable

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


def _remote_tracking_ref(branch: str) -> str:
    return f"refs/remotes/origin/{branch}"


class GitService:
    def __init__(self, git_client: GitClient):
        self._git_client = git_client

    def build_commit_context(
        self,
        recent_commit_limit: int = 10,
    ) -> CommitContext:
        return CommitContext(
            branch=self._git_client.current_branch(),
            staged_diff=self._git_client.staged_diff(),
            recent_commits=self._git_client.recent_commits(
                limit=recent_commit_limit,
            ),
        )

    def build_pull_request_context(
        self,
        base_branch: str,
        base_ref: str | None = None,
    ) -> PullRequestContext:
        """Collect what the pull request changes relative to its base.

        `base_ref` is what to compare against (usually origin/<base>, from
        base_comparison_ref); `base_branch` is the name GitHub knows the base by.
        """

        compare_to = base_ref or base_branch
        head_branch = self._git_client.current_branch()
        merge_base = self._git_client.merge_base(
            compare_to,
            head_branch,
        )
        commits = self._git_client.commits_between(
            compare_to,
            head_branch,
        )
        changed_files = self._git_client.changed_files(
            compare_to,
            head_branch,
        )
        diff = self._git_client.branch_diff(
            compare_to,
            head_branch,
        )

        return PullRequestContext(
            current_branch=head_branch,
            base_branch=base_branch,
            merge_base=merge_base,
            commits=commits,
            changed_files=changed_files,
            diff=diff,
        )

    def resolve_base_branch(self, base_branch: str | None = None) -> str:
        """Resolve the base branch for a pull request."""

        current_branch = self._git_client.current_branch()

        if not current_branch:
            raise DetachedHeadError("Cannot generate a pull request from a detached HEAD.")

        branches = self._git_client.branches()

        def exists(branch: str) -> bool:
            # Cheapest first: a local branch, a remote-tracking branch, then asking origin,
            # so a base that only exists on origin (never checked out) is accepted.
            return (
                branch in branches
                or self._git_client.ref_exists(_remote_tracking_ref(branch))
                or self._git_client.remote_has_branch(branch) is True
            )

        if base_branch is not None:
            if not exists(base_branch):
                raise BaseBranchNotFoundError(
                    f"Base branch '{base_branch}' does not exist locally or on origin."
                )

            resolved_base = base_branch

        else:
            default_branch = self._git_client.default_branch()

            if default_branch is not None:
                resolved_base = default_branch
            elif exists("main"):
                resolved_base = "main"
            elif exists("master"):
                resolved_base = "master"
            else:
                raise BaseBranchNotFoundError(
                    "Could not determine a base branch automatically."
                    "Specify one explicitly with 'diffsage pr <base-branch>'."
                )

        if resolved_base == current_branch:
            raise SameBranchError("Current branch and base branch are the same.")

        return resolved_base

    def base_comparison_ref(
        self,
        base_branch: str,
        on_notice: Callable[[str], None] | None = None,
    ) -> str:
        """Return the ref to compare the pull request against, fetched fresh from origin.

        GitHub compares a pull request with the base branch on origin, not with the local
        copy, which may be out of date. When origin cannot be fetched, the last fetched
        origin/<base> (or, failing that, the local branch) is used with a notice.
        """

        on_origin = self._git_client.remote_has_branch(base_branch)

        if on_origin is False:
            raise BaseBranchNotFoundError(
                f"Base branch '{base_branch}' does not exist on origin, so GitHub cannot open "
                "a pull request against it. Push it first, or choose another base branch."
            )

        reason = "origin could not be reached"

        if on_origin:
            try:
                self._git_client.fetch_branch(base_branch)
                return _remote_tracking_ref(base_branch)
            except FetchFailedError as error:
                reason = error.message

        def notify(message: str) -> None:
            if on_notice is not None:
                on_notice(message)

        if self._git_client.ref_exists(_remote_tracking_ref(base_branch)):
            notify(
                f"Could not update origin/{base_branch} ({reason}). Comparing against "
                f"origin/{base_branch} as last fetched, which may be out of date."
            )
            return _remote_tracking_ref(base_branch)

        if base_branch in self._git_client.branches():
            notify(
                f"Could not fetch {base_branch} from origin ({reason}). Comparing against your "
                f"local {base_branch}, which may be out of date."
            )
            return base_branch

        raise BaseBranchNotFoundError(
            f"Could not fetch base branch '{base_branch}' from origin ({reason})."
        )

    def current_branch(self) -> str:
        branch = self._git_client.current_branch()

        if not branch:
            raise DetachedHeadError("Cannot generate a pull request from detached HEAD.")

        return branch

    def validate_remote_head(self, branch: str) -> None:
        """Ensure the local branch and its copy on origin point at the same commit.

        When they differ, say which side is behind, because the fix differs: push,
        pull, or pull and then push.
        """

        local_head = self._git_client.current_commit()
        remote_head = self._git_client.remote_branch_commit(branch)

        if remote_head is None:
            if self._git_client.remote_has_branch(branch) is None:
                raise RemoteUnavailableError(
                    f"Could not reach origin to check branch '{branch}'. Check your network "
                    "connection and access to the repository, then try again."
                )

            raise RemoteBranchNotFoundError(
                f"Branch '{branch}' does not exist on origin. Push it first: "
                f"git push -u origin {branch}"
            )

        if local_head == remote_head:
            return

        if self._git_client.is_ancestor(remote_head, local_head):
            raise UnpushedChangesError(
                f"Local branch '{branch}' has commits that have not been pushed to origin. "
                "Push them first: git push"
            )

        # Origin's commit is not part of the local branch. If it was never fetched,
        # fetch it so we can tell "behind" from "diverged".
        if not self._git_client.ref_exists(remote_head):
            try:
                self._git_client.fetch_branch(branch)
            except FetchFailedError:
                pass

        behind = self._git_client.is_ancestor(local_head, remote_head)

        if behind is False:
            raise BranchesDivergedError(
                f"Local branch '{branch}' and origin/{branch} have diverged: each has commits "
                "the other does not. Combine them first (git pull --rebase, or git pull), "
                "then push: git push"
            )

        raise RemoteAheadError(
            f"origin/{branch} has commits that your local branch does not have. Pull them "
            "first: git pull"
        )
