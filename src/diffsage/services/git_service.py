from diffsage.git.client import GitClient
from diffsage.models.git import CommitContext


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
