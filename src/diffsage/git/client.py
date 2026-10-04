import subprocess
from datetime import datetime
from pathlib import Path

from diffsage.exceptions import CommitFailedError
from diffsage.models.git import GitCommit

# hash, author, ISO date, subject. The subject goes last because it is the only field
# that may contain a tab, so each line is split at most three times.
_LOG_FORMAT = "%H%x09%an%x09%aI%x09%s"


def _parse_log(output: str) -> list[GitCommit]:
    commits: list[GitCommit] = []

    for line in output.splitlines():
        hash_, author, date, message = line.split("\t", 3)
        commits.append(
            GitCommit(hash=hash_, author=author, message=message, date=datetime.fromisoformat(date))
        )

    return commits


class GitClient:
    """Low-level client for executing Git commands."""

    def __init__(self, repo_path: Path | str | None = None) -> None:
        self._repo_path = Path(repo_path) if repo_path else Path.cwd()

    def _run_git_command(
        self, args: list[str], input_text: str | None = None
    ) -> subprocess.CompletedProcess[str]:
        """Execute a Git command and return the completed process.

        Git reads and writes UTF-8 by default. Setting it explicitly avoids the system code
        page (cp1252 on many Windows machines) garbling non-ASCII text; invalid bytes, such
        as from a binary-ish file in a diff, are replaced instead of raising.
        """

        return subprocess.run(
            ["git", *args],
            cwd=self._repo_path,
            input=input_text,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
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

    def staged_diff(self) -> str:
        """Returns the staged diff"""

        result = self._run_git_command(
            ["diff", "--staged"],
        )
        return result.stdout.strip()

    def has_commits(self) -> bool:
        """Return True if HEAD points at a commit (False in a brand-new repository)."""

        try:
            self._run_git_command(["rev-parse", "--verify", "--quiet", "HEAD"])
            return True
        except subprocess.CalledProcessError:
            return False

    def recent_commits(self, limit: int = 10) -> list[GitCommit]:
        """Return the most recent commits, or none if the repository has no commits yet."""

        if not self.has_commits():
            return []

        result = self._run_git_command(["log", f"-{limit}", f"--format={_LOG_FORMAT}"])

        return _parse_log(result.stdout)

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
        """Create a commit with exactly this message.

        The message goes through stdin (`-F -`) rather than `-m` arguments: no command-line
        length limit (32,767 characters on Windows), and nothing visible in `ps`.
        """

        try:
            self._run_git_command(["commit", "-F", "-"], input_text=message)

        except subprocess.CalledProcessError as error:
            # Hooks print to stderr, but some git failures (e.g. "nothing to commit") go
            # to stdout, so both are shown.
            output = "\n".join(
                part.strip() for part in (error.stdout, error.stderr) if part and part.strip()
            )

            if not output:
                output = f"git exited with status {error.returncode}."

            raise CommitFailedError(
                "git commit failed. Nothing was committed; the message is shown above.\n" + output
            ) from error

    def merge_base(self, base_branch: str, head_branch: str) -> str:
        """Return the common ancestor commit hash of two branches."""

        result = self._run_git_command(
            ["merge-base", base_branch, head_branch],
        )

        return result.stdout.strip()

    def commits_between(self, base_branch: str, head_branch: str) -> list[GitCommit]:
        """Return commits reachable from the head branch but not the base branch."""

        result = self._run_git_command(
            ["log", f"--format={_LOG_FORMAT}", f"{base_branch}..{head_branch}"],
        )

        return _parse_log(result.stdout)

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

    def remote_branch_commit(self, branch: str) -> str | None:
        """Return the commit hash of the remote origin branch."""

        try:
            result = self._run_git_command(["ls-remote", "origin", f"refs/heads/{branch}"])
        except subprocess.CalledProcessError:
            return None

        output = result.stdout.strip()

        if not output:
            return None

        return output.split("\t", 1)[0]
