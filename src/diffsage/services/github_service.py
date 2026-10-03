import subprocess

from diffsage.exceptions import (
    GitHubAuthenticationError,
    GitHubCLIUnavailableError,
    GitHubError,
)
from diffsage.github.client import GitHubClient
from diffsage.models.pull_request import PullRequestDraft


class GitHubService:
    def __init__(self, github_client: GitHubClient) -> None:
        self._github_client = github_client

    def _build_list_section(
        self,
        title: str,
        values: list[str],
    ) -> str:
        if not values:
            values = ["None."]

        items = "\n".join(f"- {value}" for value in values)

        return f"## {title}\n{items}"

    def _build_pull_request_body(
        self,
        draft: PullRequestDraft,
    ) -> str:
        sections = [
            f"## Summary\n{draft.summary}",
            f"## Why\n{draft.why}",
            self._build_list_section("Changes", draft.changes),
            self._build_list_section("Testing", draft.testing),
            self._build_list_section("Risks", draft.risks),
            self._build_list_section(
                "Reviewer Focus",
                draft.reviewer_focus,
            ),
            self._build_list_section(
                "Breaking Changes",
                draft.breaking_changes,
            ),
        ]

        return "\n\n".join(sections)

    def validate(self) -> None:
        """Validate that GitHub CLI is available and authenticated."""

        if not self._github_client.is_available():
            raise GitHubCLIUnavailableError(
                "GitHub CLI is not installed. Install it and try again."
            )

        if not self._github_client.is_authenticated():
            raise GitHubAuthenticationError(
                "GitHub CLI is not authenticated. Run 'gh auth login' and try again."
            )

    def create_pull_request(
        self,
        draft: PullRequestDraft,
        base_branch: str,
        head_branch: str,
    ) -> str:
        """Create a GitHub pull request from a generated draft."""

        body = self._build_pull_request_body(draft)

        try:
            return self._github_client.create_pull_request(
                title=draft.title,
                body=body,
                base_branch=base_branch,
                head_branch=head_branch,
            )
        except subprocess.CalledProcessError as error:
            details = (error.stderr or "").strip()

            if not details:
                details = f"gh exited with status {error.returncode}."

            raise GitHubError(f"GitHub CLI could not create the pull request: {details}") from error
