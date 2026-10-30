import subprocess
from unittest.mock import Mock

import pytest

from diffsage.exceptions.github import (
    GitHubAuthenticationError,
    GitHubCLIUnavailableError,
    GitHubError,
)
from diffsage.github.client import GitHubClient
from diffsage.models.pull_request import PullRequestDraft
from diffsage.services.github_service import GitHubService


def create_pull_request_draft() -> PullRequestDraft:
    return PullRequestDraft(
        title="Add pull request generation",
        summary="Adds structured pull request generation.",
        why="Provides developers with generated PR drafts.",
        changes=[
            "Add pull request orchestration.",
            "Add deterministic PR analysis.",
        ],
        testing=[
            "Run unit tests.",
            "Run full test suite.",
        ],
        risks=[
            "Changes affect the public CLI.",
        ],
        reviewer_focus=[
            "Review command behavior.",
        ],
        breaking_changes=[
            "None.",
        ],
    )


def create_service() -> tuple[GitHubService, Mock]:
    github_client = Mock(spec=GitHubClient)

    service = GitHubService(
        github_client=github_client,
    )

    return service, github_client


def test_validate_succeeds_when_github_cli_is_available() -> None:
    service, github_client = create_service()

    github_client.is_available.return_value = True

    service.validate()

    github_client.is_available.assert_called_once()


def test_validate_raises_when_github_cli_is_unavailable() -> None:
    service, github_client = create_service()

    github_client.is_available.return_value = False

    with pytest.raises(GitHubCLIUnavailableError):
        service.validate()

    github_client.is_available.assert_called_once()


def test_open_pull_request_check_reports_a_missing_login() -> None:
    """gh exits with 4 when a command needs a login: the same request that looks for an
    open pull request also tells us whether gh is logged in."""

    service, github_client = create_service()
    github_client.open_pull_request_url.side_effect = subprocess.CalledProcessError(
        4, ["gh", "pr", "list"], stderr="To get started with GitHub CLI, please run: gh auth login"
    )

    with pytest.raises(GitHubAuthenticationError, match="gh auth login"):
        service.ensure_no_open_pull_request("feature", "main")


def test_open_pull_request_check_carries_on_after_other_gh_failures() -> None:
    service, github_client = create_service()
    github_client.open_pull_request_url.side_effect = subprocess.CalledProcessError(
        1, ["gh", "pr", "list"], stderr="HTTP 502"
    )

    service.ensure_no_open_pull_request("feature", "main")


def test_create_pull_request_creates_pull_request() -> None:
    service, github_client = create_service()

    github_client.is_available.return_value = True
    github_client.create_pull_request.return_value = "https://github.com/example/repo/pull/42"

    draft = create_pull_request_draft()

    result = service.create_pull_request(
        draft=draft,
        base_branch="main",
        head_branch="feature/pr-generation",
    )

    assert result == "https://github.com/example/repo/pull/42"

    github_client.create_pull_request.assert_called_once_with(
        title=draft.title,
        body=(
            "## Summary\n"
            "Adds structured pull request generation.\n\n"
            "## Why\n"
            "Provides developers with generated PR drafts.\n\n"
            "## Changes\n"
            "- Add pull request orchestration.\n"
            "- Add deterministic PR analysis.\n\n"
            "## Testing\n"
            "- Run unit tests.\n"
            "- Run full test suite.\n\n"
            "## Risks\n"
            "- Changes affect the public CLI.\n\n"
            "## Reviewer Focus\n"
            "- Review command behavior.\n\n"
            "## Breaking Changes\n"
            "- None."
        ),
        base_branch="main",
        head_branch="feature/pr-generation",
    )


def test_create_pull_request_reports_gh_stderr_as_github_error() -> None:
    service, github_client = create_service()
    github_client.create_pull_request.side_effect = subprocess.CalledProcessError(
        1, ["gh", "pr", "create"], stderr="  a pull request already exists\n"
    )

    with pytest.raises(GitHubError) as error:
        service.create_pull_request(create_pull_request_draft(), "main", "feature")

    assert str(error.value) == (
        "GitHub CLI could not create the pull request: a pull request already exists"
    )
    assert isinstance(error.value.__cause__, subprocess.CalledProcessError)


def test_create_pull_request_reports_exit_status_when_gh_is_silent() -> None:
    service, github_client = create_service()
    github_client.create_pull_request.side_effect = subprocess.CalledProcessError(
        4, ["gh", "pr", "create"], stderr=""
    )

    with pytest.raises(GitHubError) as error:
        service.create_pull_request(create_pull_request_draft(), "main", "feature")

    assert str(error.value) == (
        "GitHub CLI could not create the pull request: gh exited with status 4."
    )


def test_create_pull_request_posts_a_filled_template_body_as_is() -> None:
    client = Mock(spec=GitHubClient)
    client.create_pull_request.return_value = "https://example/pull/1"
    draft = PullRequestDraft(title="Add retries", summary="", why="", body="## What\nRetries.")

    GitHubService(client).create_pull_request(draft, base_branch="main", head_branch="feature")

    assert client.create_pull_request.call_args.kwargs["body"] == "## What\nRetries."
