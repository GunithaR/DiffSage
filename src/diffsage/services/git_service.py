from diffsage.exceptions import (
    BaseBranchNotFoundError,
    DetachedHeadError,
    RemoteBranchNotFoundError,
    SameBranchError,
    UnpushedChangesError,
)
from diffsage.git.client import GitClient
from diffsage.models.git import CommitContext, PullRequestContext


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
    ) -> PullRequestContext:
        head_branch = self._git_client.current_branch()
        merge_base = self._git_client.merge_base(
            base_branch,
            head_branch,
        )
        commits = self._git_client.commits_between(
            base_branch,
            head_branch,
        )
        changed_files = self._git_client.changed_files(
            base_branch,
            head_branch,
        )
        diff = self._git_client.branch_diff(
            base_branch,
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

        if base_branch is not None:
            if base_branch not in branches:
                raise BaseBranchNotFoundError(f"Base branch {base_branch} does not exist.")

            resolved_base = base_branch

        else:
            default_branch = self._git_client.default_branch()

            if default_branch is not None:
                resolved_base = default_branch
            elif "main" in branches:
                resolved_base = "main"
            elif "master" in branches:
                resolved_base = "master"
            else:
                raise BaseBranchNotFoundError(
                    "Could not determine a base branch automatically."
                    "Specify one explicitly with 'diffsage pr <base-branch>'."
                )

        if resolved_base == current_branch:
            raise SameBranchError("Current branch and base branch are the same.")

        return resolved_base

    def current_branch(self) -> str:
        branch = self._git_client.current_branch()

        if not branch:
            raise DetachedHeadError("Cannot generate a pull request from detached HEAD.")

        return branch

    def validate_remote_head(self, branch: str) -> None:
        """Ensure the local branch is synchronized with origin."""

        local_head = self._git_client.current_commit()
        remote_head = self._git_client.remote_branch_commit(branch)

        if remote_head is None:
            raise RemoteBranchNotFoundError(f"Remote branch '{branch}' does not exist on origin.")

        if local_head != remote_head:
            raise UnpushedChangesError(
                f"Local branch '{branch}' contains commits that have not been pushed to origin."
            )
