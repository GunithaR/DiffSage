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

