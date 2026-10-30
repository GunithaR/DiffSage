import subprocess
from datetime import datetime
from pathlib import Path

from diffsage.exceptions import CommitFailedError, FetchFailedError
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
        # Branches on origin, read once per client (one network round trip); None after
        # a failed read means origin could not be reached.
        self._remote_heads: dict[str, str] | None = None
        self._remote_heads_read = False

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

    def remote_heads(self) -> dict[str, str] | None:
        """Every branch on origin with its commit, or None if origin could not be reached.

        Read with a single `git ls-remote` and kept for the life of this client, so the
        branch checks of one command cost one network round trip instead of one each.
        """

        if not self._remote_heads_read:
            self._remote_heads_read = True

            try:
                result = self._run_git_command(["ls-remote", "--heads", "origin"])
            except subprocess.CalledProcessError:
                self._remote_heads = None
            else:
                self._remote_heads = {
                    ref.removeprefix("refs/heads/"): commit
                    for commit, _tab, ref in (
                        line.partition("\t") for line in result.stdout.splitlines()
                    )
                    if ref.startswith("refs/heads/")
                }

        return self._remote_heads

    def remote_has_branch(self, branch: str) -> bool | None:
        """Whether origin has the branch, or None if origin could not be reached."""

        heads = self.remote_heads()
        return None if heads is None else branch in heads

    def remote_branch_exists(self, branch: str) -> bool:
        """Return True if the branch exists on the origin remote."""

        return self.remote_has_branch(branch) is True

    def fetch_branch(self, branch: str) -> None:
        """Update the remote-tracking branch origin/<branch> from origin."""

        try:
            self._run_git_command(
                [
                    "fetch",
                    "--quiet",
                    "--no-tags",
                    "origin",
                    # "+": follow origin exactly, even if the branch was force-pushed.
                    f"+refs/heads/{branch}:refs/remotes/origin/{branch}",
                ]
            )
        except subprocess.CalledProcessError as error:
            lines = [line.strip() for line in (error.stderr or "").splitlines() if line.strip()]
            raise FetchFailedError(lines[-1] if lines else None) from error

    def list_files(self, ref: str, directory: str | None = None) -> list[str]:
        """Paths of the entries directly inside `directory` (default: the root) at `ref`."""

        args = ["ls-tree", "--name-only", ref]

        if directory is not None:
            args += ["--", f"{directory.rstrip('/')}/"]

        try:
            result = self._run_git_command(args)
        except subprocess.CalledProcessError:
            return []

        return result.stdout.splitlines()

    def read_file(self, ref: str, path: str) -> str | None:
        """Contents of `path` at `ref`, or None if it does not exist there."""

        try:
            result = self._run_git_command(["show", f"{ref}:{path}"])
        except subprocess.CalledProcessError:
            return None

        return result.stdout

    def is_ancestor(self, ancestor: str, descendant: str) -> bool | None:
        """Whether commit `ancestor` is contained in `descendant`, or None if either
        commit is not in this repository (for example, not fetched yet)."""

        try:
            self._run_git_command(["merge-base", "--is-ancestor", ancestor, descendant])
        except subprocess.CalledProcessError as error:
            # Status 1 is a plain "no"; anything else means Git could not tell.
            return False if error.returncode == 1 else None

        return True

    def ref_exists(self, ref: str) -> bool:
        """Return True if `ref` names a commit in this repository."""

        try:
            self._run_git_command(["rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}"])
        except subprocess.CalledProcessError:
            return False

        return True

    def remote_branch_commit(self, branch: str) -> str | None:
        """Return the commit hash of the remote origin branch."""

        heads = self.remote_heads()
        return None if heads is None else heads.get(branch)
