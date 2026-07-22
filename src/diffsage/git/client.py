from pathlib import Path
import subprocess

from diffsage.models.git import GitStatus

class GitClient:
    """Low-level client for executing Git commands."""

    def __init__(self, repo_path: Path | str |None = None) -> None:
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
            result = self._run_git_command(
                ["rev-parse", "--is-inside-work-tree"]
            )
            return result.stdout.strip() == "true"
        
        except subprocess.CalledProcessError:
            return False
        
    def repository_root(self) -> Path:
        """Return the root directory of the Git repository."""

        result = self._run_git_command(
            ["rev-parse", "--show-toplevel"]
        )
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