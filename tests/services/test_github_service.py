from unittest.mock import Mock

import pytest

from diffsage.exceptions.github import (
    GitHubAuthenticationError,
    GitHubCLIUnavailableError,
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


def test_validate_succeeds_when_github_cli_is_available_and_authenticated() -> None:
    service, github_client = create_service()

    github_client.is_available.return_value = True
    github_client.is_authenticated.return_value = True

    service.validate()

    github_client.is_available.assert_called_once()
    github_client.is_authenticated.assert_called_once()


def test_validate_raises_when_github_cli_is_unavailable() -> None:
    service, github_client = create_service()

    github_client.is_available.return_value = False

    with pytest.raises(GitHubCLIUnavailableError):
        service.validate()

    github_client.is_available.assert_called_once()
    github_client.is_authenticated.assert_not_called()


def test_validate_raises_when_github_cli_is_not_authenticated() -> None:
    service, github_client = create_service()

    github_client.is_available.return_value = True
    github_client.is_authenticated.return_value = False

    with pytest.raises(GitHubAuthenticationError):
        service.validate()

    github_client.is_available.assert_called_once()
    github_client.is_authenticated.assert_called_once()


def test_create_pull_request_creates_pull_request() -> None:
    service, github_client = create_service()

    github_client.is_available.return_value = True
    github_client.is_authenticated.return_value = True
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
