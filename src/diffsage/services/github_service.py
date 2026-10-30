import subprocess

from diffsage.exceptions import (
    GitHubAuthenticationError,
    GitHubCLIUnavailableError,
    GitHubError,
    PullRequestExistsError,
)
from diffsage.github.client import GitHubClient
from diffsage.logging.logger import get_logger
from diffsage.models.pull_request import PullRequestDraft

logger = get_logger(__name__)


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

    def ensure_no_open_pull_request(self, head_branch: str, base_branch: str) -> None:
        """Stop before drafting if the branch already has an open pull request.

        GitHub allows one open pull request per branch pair, so a new draft could
        never be created. If the check itself fails, carry on: `gh pr create` still
        reports any problem at the end.
        """

        try:
            url = self._github_client.open_pull_request_url(head_branch, base_branch)
        except (subprocess.CalledProcessError, ValueError) as error:
            logger.warning("Could not check for an open pull request: %s", error)
            return

        if url:
            raise PullRequestExistsError(
                f"A pull request from '{head_branch}' into '{base_branch}' is already open: {url}"
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
