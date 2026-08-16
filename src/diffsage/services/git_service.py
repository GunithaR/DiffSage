from diffsage.git.client import GitClient
from diffsage.models.git import CommitContext, PullRequestContext
from diffsage.exceptions import BaseBranchNotFoundError


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
            unstaged_diff=self._git_client.unstaged_diff(),
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

    def resolve_base_branch(
        self,
        base_branch: str | None = None
    ) -> str:
        """Resolve the base branch for a pull request."""

        branches = self._git_client.branches()

        if base_branch is not None:
            if base_branch not in branches:
                raise BaseBranchNotFoundError(
                    f"Base branch {base_branch} does not exist."
                )

            return base_branch

        default_branch = self._git_client.default_branch()

        if default_branch is not None:
            return default_branch

        if "main" in branches:
            return "main"

        if "master" in branches:
            return "master"

        raise BaseBranchNotFoundError(
            "Could not determine a base branch automatically." \
            "Specify one explicitly with 'diffsage pr <base-branch>'."
        )