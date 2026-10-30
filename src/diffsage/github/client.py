import json
import subprocess
from pathlib import Path


class GitHubClient:
    """Low-level client for executing GitHub CLI commands."""

    def __init__(self, repo_path: Path | str | None = None) -> None:
        self._repo_path = Path(repo_path) if repo_path else Path.cwd()

    def _run_gh_command(
        self,
        args: list[str],
        input_text: str | None = None,
    ) -> subprocess.CompletedProcess[str]:
        """Execute a GitHub CLI command and return the completed process.

        gh reads and writes UTF-8; setting it explicitly stops Windows from decoding
        its output with the system code page (cp1252), which garbles non-ASCII text.
        """

        return subprocess.run(
            ["gh", *args],
            cwd=self._repo_path,
            input=input_text,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=True,
        )

    def is_available(self) -> bool:
        """Return True if the GitHub CLI is installed."""

        try:
            self._run_gh_command(["--version"])
            return True
        except FileNotFoundError:
            return False

    def open_pull_request_url(self, head_branch: str, base_branch: str) -> str | None:
        """URL of the open pull request from `head_branch` into `base_branch`, if any."""

        result = self._run_gh_command(
            [
                "pr",
                "list",
                "--head",
                head_branch,
                "--base",
                base_branch,
                "--state",
                "open",
                "--json",
                "number,url",
                "--limit",
                "1",
            ]
        )
        pull_requests = json.loads(result.stdout or "[]")

        if isinstance(pull_requests, list) and pull_requests:
            url = pull_requests[0].get("url") if isinstance(pull_requests[0], dict) else None
            return url if isinstance(url, str) else None

        return None

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
                # The body goes through stdin rather than the command line, which on
                # Windows is limited to 32,767 characters.
                "--body-file",
                "-",
            ],
            input_text=body,
        )

        return result.stdout.strip()
