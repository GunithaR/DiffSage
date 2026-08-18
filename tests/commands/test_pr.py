from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from diffsage.cli import app
from diffsage.commands.pr import pr
from diffsage.exceptions import (
    BaseBranchNotFoundError,
    ConfigError,
    CredentialNotFoundError,
    DetachedHeadError,
    NotGitRepositoryError,
    ProviderError,
    SameBranchError,
)
from diffsage.models.pull_request import PullRequestDraft

runner = CliRunner()


def create_pull_request_draft() -> PullRequestDraft:
    return PullRequestDraft(
        title="Add pull request generation",
        summary="Adds pull request generation.",
        why="Provides structured pull request drafts.",
        changes=[
            "Add pull request generation.",
        ],
        testing=[
            "Added unit tests.",
        ],
        risks=[],
        reviewer_focus=[],
        breaking_changes=[],
    )


def test_pr_generates_and_displays_draft():
    with (
        patch("diffsage.commands.pr.GitClient"),
        patch("diffsage.commands.pr.GitService") as mock_git_service,
        patch("diffsage.commands.pr.PullRequestService") as mock_pr_service,
        patch("diffsage.commands.pr.load_settings") as mock_load_settings,
        patch("diffsage.commands.pr.AIService") as mock_ai_service,
        patch("diffsage.commands.pr.get_credentials_path") as mock_get_path,
        patch("diffsage.commands.pr.CredentialsRepository") as mock_repository,
        patch("diffsage.commands.pr.CredentialService") as mock_credential_service,
        patch("diffsage.commands.pr.PullRequestView") as mock_view,
    ):
        settings = mock_load_settings.return_value
        repository = mock_repository.return_value
        credential_service = mock_credential_service.return_value

        mock_git_service.return_value.resolve_base_branch.return_value = "main"

        draft = create_pull_request_draft()
        mock_pr_service.return_value.generate_draft.return_value = draft

        result = runner.invoke(app, ["pr"])

        assert result.exit_code == 0

        mock_git_service.return_value.resolve_base_branch.assert_called_once_with(None)
        mock_pr_service.return_value.generate_draft.assert_called_once_with("main")
        mock_view.return_value.show_generated.assert_called_once_with(draft)

        mock_get_path.assert_called_once()
        mock_repository.assert_called_once_with(mock_get_path.return_value)
        mock_credential_service.assert_called_once_with(repository)
        mock_ai_service.assert_called_once_with(
            settings,
            credential_service,
        )


def test_pr_uses_explicit_base_branch():
    with (
        patch("diffsage.commands.pr.GitClient"),
        patch("diffsage.commands.pr.GitService") as mock_git_service,
        patch("diffsage.commands.pr.PullRequestService") as mock_pr_service,
        patch("diffsage.commands.pr.load_settings"),
        patch("diffsage.commands.pr.AIService"),
        patch("diffsage.commands.pr.get_credentials_path"),
        patch("diffsage.commands.pr.CredentialsRepository"),
        patch("diffsage.commands.pr.CredentialService"),
        patch("diffsage.commands.pr.PullRequestView") as mock_view,
    ):
        mock_git_service.return_value.resolve_base_branch.return_value = "develop"

        draft = create_pull_request_draft()
        mock_pr_service.return_value.generate_draft.return_value = draft

        result = runner.invoke(app, ["pr", "develop"])

        assert result.exit_code == 0

        mock_git_service.return_value.resolve_base_branch.assert_called_once_with("develop")
        mock_pr_service.return_value.generate_draft.assert_called_once_with("develop")
        mock_view.return_value.show_generated.assert_called_once_with(draft)


def test_pr_exits_when_not_in_git_repository():
    with patch("diffsage.commands.pr.GitClient") as mock_git:
        mock_git.side_effect = NotGitRepositoryError("Not a Git repository.")

        with pytest.raises(SystemExit):
            pr()


def test_pr_exits_when_head_is_detached():
    with (
        patch("diffsage.commands.pr.GitClient"),
        patch("diffsage.commands.pr.GitService") as mock_git_service,
        patch("diffsage.commands.pr.PullRequestView") as mock_view,
    ):
        mock_git_service.return_value.resolve_base_branch.side_effect = DetachedHeadError(
            "Cannot generate a pull request from detached HEAD."
        )

        with pytest.raises(SystemExit):
            pr()

        mock_view.return_value.show_detached_head.assert_called_once()


def test_pr_exits_when_base_branch_cannot_be_resolved():
    with (
        patch("diffsage.commands.pr.GitClient"),
        patch("diffsage.commands.pr.GitService") as mock_git_service,
        patch("diffsage.commands.pr.PullRequestView") as mock_view,
    ):
        mock_git_service.return_value.resolve_base_branch.side_effect = BaseBranchNotFoundError(
            "Could not determine a base branch."
        )

        with pytest.raises(SystemExit):
            pr()

        mock_view.return_value.show_base_branch_not_found.assert_called_once()


def test_pr_exits_when_base_branch_is_current_branch():
    with (
        patch("diffsage.commands.pr.GitClient"),
        patch("diffsage.commands.pr.GitService") as mock_git_service,
        patch("diffsage.commands.pr.PullRequestView") as mock_view,
    ):
        mock_git_service.return_value.resolve_base_branch.side_effect = SameBranchError(
            "Current branch and base branch are the same."
        )

        with pytest.raises(SystemExit):
            pr()

        mock_view.return_value.show_same_branch.assert_called_once()


def test_pr_exits_when_credential_is_missing():
    with (
        patch("diffsage.commands.pr.GitClient"),
        patch("diffsage.commands.pr.load_settings"),
        patch("diffsage.commands.pr.get_credentials_path"),
        patch("diffsage.commands.pr.CredentialsRepository"),
        patch("diffsage.commands.pr.CredentialService"),
        patch("diffsage.commands.pr.AIService") as mock_ai_service,
        patch("diffsage.commands.pr.PullRequestView") as mock_view,
    ):
        mock_ai_service.side_effect = CredentialNotFoundError("Credential not found.")

        with pytest.raises(SystemExit):
            pr()

        mock_view.return_value.show_error.assert_called_once_with(
            "Credential not found for provider 'Credential not found.' and profile 'default'."
        )


def test_pr_exits_on_provider_error():
    with (
        patch("diffsage.commands.pr.GitClient"),
        patch("diffsage.commands.pr.load_settings"),
        patch("diffsage.commands.pr.get_credentials_path"),
        patch("diffsage.commands.pr.CredentialsRepository"),
        patch("diffsage.commands.pr.CredentialService"),
        patch("diffsage.commands.pr.AIService") as mock_ai_service,
        patch("diffsage.commands.pr.PullRequestView") as mock_view,
    ):
        mock_ai_service.side_effect = ProviderError("Provider unavailable.")

        with pytest.raises(SystemExit):
            pr()

        mock_view.return_value.show_error.assert_called_once_with("Provider unavailable.")


def test_pr_exits_on_configuration_error():
    with (
        patch("diffsage.commands.pr.GitClient"),
        patch("diffsage.commands.pr.load_settings") as mock_load_settings,
        patch("diffsage.commands.pr.PullRequestView") as mock_view,
    ):
        mock_load_settings.side_effect = ConfigError("Invalid configuration.")

        with pytest.raises(SystemExit):
            pr()

        mock_view.return_value.show_error.assert_called_once_with("Invalid configuration.")


def test_pr_handles_unexpected_error():
    with (
        patch("diffsage.commands.pr.GitClient") as mock_git,
        patch("diffsage.commands.pr.PullRequestView") as mock_view,
    ):
        mock_git.side_effect = RuntimeError("Unexpected failure")

        with pytest.raises(SystemExit):
            pr()

        mock_view.return_value.show_error.assert_called_once_with(
            "An unexpected error occurred. Please check the log file for more details."
        )
