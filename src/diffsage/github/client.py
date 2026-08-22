import subprocess
from pathlib import Path


class GitHubClient:
    """Low-level client for executing GitHub CLI commands."""

    def __init__(self, repo_path: Path | str | None = None) -> None:
        self._repo_path = Path(repo_path) if repo_path else Path.cwd()

    def _run_gh_command(
        self,
        args: list[str],
    ) -> subprocess.CompletedProcess[str]:
        """Execute a GitHub CLI command and return the completed process."""

        return subprocess.run(
            ["gh", *args],
            cwd=self._repo_path,
            capture_output=True,
            text=True,
            check=True,
        )

    def is_available(self) -> bool:
        """Return True if the GitHub CLI is installed."""

        try:
            self._run_gh_command(["--version"])
            return True
        except FileNotFoundError:
            return False

    def is_authenticated(self) -> bool:
        """Return True if the user is authenticated with GitHub."""

        try:
            self._run_gh_command(["auth", "status"])
            return True
        except subprocess.CalledProcessError:
            return False

    def create_pull_request(
        self,
        title: str,
        body: str,
        base_branch: str,
        head_branch: str,
    ) -> str:
        result = self._run_gh_command(
            [
                "pr",
                "create",
                "--base",
                base_branch,
                "--head",
                head_branch,
                "--title",
                title,
                "--body",
                body,
            ]
        )

        return result.stdout.strip()
