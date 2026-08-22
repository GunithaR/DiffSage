import subprocess
from datetime import datetime
from pathlib import Path

from diffsage.models.git import GitCommit, GitStatus


class GitClient:
    """Low-level client for executing Git commands."""

    def __init__(self, repo_path: Path | str | None = None) -> None:
        self._repo_path = Path(repo_path) if repo_path else Path.cwd()

    def _run_git_command(self, args: list[str]) -> subprocess.CompletedProcess[str]:
        """Execute a Git command and return the completed process."""

        return subprocess.run(
            ["git", *args],
            cwd=self._repo_path,
            capture_output=True,
            text=True,
            check=True,
        )

    def is_git_repository(self) -> bool:
        """Return True if the repository path is inside a Git working tree."""
        try:
            result = self._run_git_command(["rev-parse", "--is-inside-work-tree"])
            return result.stdout.strip() == "true"

        except subprocess.CalledProcessError:
            return False

    def repository_root(self) -> Path:
        """Return the root directory of the Git repository."""

        result = self._run_git_command(["rev-parse", "--show-toplevel"])
        return Path(result.stdout.strip())

    def current_branch(self) -> str:
        """Return the name of the current Git branch."""

        result = self._run_git_command(
            ["branch", "--show-current"],
        )
        return result.stdout.strip()

    def current_commit(self) -> str:
        """Return the hash of the current commit."""

        result = self._run_git_command(
            ["rev-parse", "HEAD"],
        )
        return result.stdout.strip()

    def status(self) -> GitStatus:
        """Return the current repository status."""

        result = self._run_git_command(
            ["status", "--porcelain"],
        )

        untracked = []
        modified = []
        added = []
        deleted = []

        # Parse Git porcelain status codes.
        for line in result.stdout.splitlines():
            status = line[:2]
            path = line[3:]

            match status:
                case "??":
                    untracked.append(path)
                case " M":
                    modified.append(path)
                case "A ":
                    added.append(path)
                case " D":
                    deleted.append(path)

        return GitStatus(
            modified=modified,
            added=added,
            deleted=deleted,
            untracked=untracked,
        )

    def staged_diff(self) -> str:
        """Returns the staged diff"""

        result = self._run_git_command(
            ["diff", "--staged"],
        )
        return result.stdout.strip()

    def unstaged_diff(self) -> str:
        """Returns the unstaged diff"""

        result = self._run_git_command(
            ["diff"],
        )
        return result.stdout.strip()

    def recent_commits(self, limit: int = 10) -> list[GitCommit]:
        """Return the most recent commits."""

        result = self._run_git_command(
            ["log", f"-{limit}", "--pretty=format:%H%x09%an%x09%s%x09%aI"],
        )

        commits: list[GitCommit] = []

        for line in result.stdout.splitlines():
            hash_, author, message, date = line.split("\t")

            commit = GitCommit(
                hash=hash_, author=author, message=message, date=datetime.fromisoformat(date)
            )
            commits.append(commit)

        return commits

    def branches(self) -> list[str]:
        """Return local branch names."""

        result = self._run_git_command(
            ["branch", "--format=%(refname:short)"],
        )

        return result.stdout.splitlines()

    def tags(self) -> list[str]:
        """Return tag names."""

        result = self._run_git_command(
            ["tag", "--format=%(refname:short)"],
        )
        return result.stdout.splitlines()

    def commit(self, message: str) -> None:
        """Create a git commit with the provided commit message."""

        lines = message.split("\n", 1)

        subject = lines[0]
        body = lines[1].strip() if len(lines) > 1 else ""

        command = ["commit", "-m", subject]

        if body:
            command.extend(["-m", body])

        self._run_git_command(command)

    def merge_base(self, base_branch: str, head_branch: str) -> str:
        """Return the common ancestor commit hash of two branches."""

        result = self._run_git_command(
            ["merge-base", base_branch, head_branch],
        )

        return result.stdout.strip()

    def commits_between(self, base_branch: str, head_branch: str) -> list[GitCommit]:
        """Return commits reachable from the head branch but not the base branch."""

        result = self._run_git_command(
            [
                "log",
                "--format=%H%x09%an%x09%s%x09%aI",
                f"{base_branch}..{head_branch}",
            ],
        )

        commits: list[GitCommit] = []

        for line in result.stdout.splitlines():
            hash_, author, message, date = line.split("\t")

            commit = GitCommit(
                hash=hash_, author=author, message=message, date=datetime.fromisoformat(date)
            )
            commits.append(commit)

        return commits

    def changed_files(self, base_branch: str, head_branch: str) -> list[str]:
        """Return file paths changed between the base and head branches."""

        merge_base = self.merge_base(base_branch, head_branch)

        result = self._run_git_command(
            ["diff", "--name-only", merge_base, head_branch],
        )

        return result.stdout.splitlines()

    def branch_diff(self, base_branch: str, head_branch: str) -> str:
        """Return the diff introduced by the head branch since the merge base."""

        merge_base = self.merge_base(base_branch, head_branch)

        result = self._run_git_command(["diff", merge_base, head_branch])

        return result.stdout

    def default_branch(self) -> str | None:
        """Return the default branch configured for the origin remote."""

        try:
            result = self._run_git_command(["symbolic-ref", "refs/remotes/origin/HEAD"])
        except subprocess.CalledProcessError:
            pass
        else:
            ref = result.stdout.strip()
            prefix = "refs/remotes/origin/"

            if ref.startswith(prefix):
                return ref.removeprefix(prefix)

        try:
            result = self._run_git_command(["ls-remote", "--symref", "origin", "HEAD"])
        except subprocess.CalledProcessError:
            return None

        for line in result.stdout.splitlines():
            if line.startswith("ref:") and line.endswith("\tHEAD"):
                ref = line.split("\t", 1)[0]
                return ref.removeprefix("ref: refs/heads/")

        return None

    def remote_branch_exists(self, branch: str) -> bool:
        """Return True if the branch exists on the origin remote."""

        try:
            self._run_git_command(["ls-remote", "--exit-code", "--heads", "origin", branch])
            return True
        except subprocess.CalledProcessError:
            return False
