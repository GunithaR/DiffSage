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
    GitHubAuthenticationError,
    GitHubCLIUnavailableError,
    InvalidPullRequestDraftError,
    NotGitRepositoryError,
    ProviderError,
    RemoteBranchNotFoundError,
    SameBranchError,
    UnpushedChangesError,
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


def test_pr_generates_and_accepts_draft():
    with (
        patch("diffsage.commands.pr.GitClient"),
        patch("diffsage.commands.pr.GitHubClient"),
        patch("diffsage.commands.pr.GitService") as mock_git_service,
        patch("diffsage.commands.pr.GitHubService") as mock_github_service,
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
        mock_git_service.return_value.current_branch.return_value = "feature/pr-generation"
        mock_git_service.return_value.validate_remote_head.return_value = None
        mock_github_service.return_value.validate.return_value = None
        mock_github_service.return_value.create_pull_request.return_value = (
            "https://github.com/example/repo/pull/42"
        )

        draft = create_pull_request_draft()
        mock_pr_service.return_value.generate_draft.return_value = draft
        mock_view.return_value.prompt_action.return_value = "y"

        result = runner.invoke(app, ["pr"])

        assert result.exit_code == 0

        mock_git_service.return_value.resolve_base_branch.assert_called_once_with(None)
        mock_github_service.return_value.validate.assert_called_once()
        mock_git_service.return_value.validate_remote_head.assert_called_once_with(
            "feature/pr-generation"
        )
        mock_github_service.return_value.create_pull_request.assert_called_once_with(
            draft=draft,
            base_branch="main",
            head_branch="feature/pr-generation",
        )

        call = mock_pr_service.return_value.generate_draft.call_args

        assert call.args == ("main",)
        assert "on_attempt" in call.kwargs
        assert callable(call.kwargs["on_attempt"])

        mock_view.return_value.show_generated.assert_called_once_with(draft)
        mock_view.return_value.prompt_action.assert_called_once()

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
        patch("diffsage.commands.pr.GitHubClient"),
        patch("diffsage.commands.pr.GitService") as mock_git_service,
        patch("diffsage.commands.pr.GitHubService") as mock_github_service,
        patch("diffsage.commands.pr.PullRequestService") as mock_pr_service,
        patch("diffsage.commands.pr.load_settings"),
        patch("diffsage.commands.pr.AIService"),
        patch("diffsage.commands.pr.get_credentials_path"),
        patch("diffsage.commands.pr.CredentialsRepository"),
        patch("diffsage.commands.pr.CredentialService"),
        patch("diffsage.commands.pr.PullRequestView") as mock_view,
    ):
        mock_git_service.return_value.resolve_base_branch.return_value = "develop"
        mock_git_service.return_value.current_branch.return_value = "feature/pr-generation"
        mock_github_service.return_value.validate.return_value = None
        mock_github_service.return_value.create_pull_request.return_value = (
            "https://github.com/example/repo/pull/42"
        )

        draft = create_pull_request_draft()
        mock_pr_service.return_value.generate_draft.return_value = draft
        mock_view.return_value.prompt_action.return_value = "y"

        result = runner.invoke(app, ["pr", "develop"])

        assert result.exit_code == 0

        mock_git_service.return_value.resolve_base_branch.assert_called_once_with("develop")
        mock_github_service.return_value.validate.assert_called_once()
        mock_github_service.return_value.create_pull_request.assert_called_once_with(
            draft=draft,
            base_branch="develop",
            head_branch="feature/pr-generation",
        )

        call = mock_pr_service.return_value.generate_draft.call_args

        assert call.args == ("develop",)
        assert "on_attempt" in call.kwargs
        assert callable(call.kwargs["on_attempt"])

        mock_view.return_value.show_generated.assert_called_once_with(draft)


def test_pr_edits_draft():
    with (
        patch("diffsage.commands.pr.GitClient"),
        patch("diffsage.commands.pr.GitHubClient"),
        patch("diffsage.commands.pr.GitService") as mock_git_service,
        patch("diffsage.commands.pr.GitHubService") as mock_github_service,
        patch("diffsage.commands.pr.PullRequestService") as mock_pr_service,
        patch("diffsage.commands.pr.load_settings"),
        patch("diffsage.commands.pr.AIService"),
        patch("diffsage.commands.pr.get_credentials_path"),
        patch("diffsage.commands.pr.CredentialsRepository"),
        patch("diffsage.commands.pr.CredentialService"),
        patch("diffsage.commands.pr.EditorService") as mock_editor,
        patch("diffsage.commands.pr.PullRequestParser") as mock_parser,
        patch("diffsage.commands.pr.PullRequestView") as mock_view,
    ):
        mock_git_service.return_value.resolve_base_branch.return_value = "main"
        mock_github_service.return_value.create_pull_request.return_value = (
            "https://github.com/example/repo/pull/42"
        )

        original_draft = create_pull_request_draft()

        edited_draft = PullRequestDraft(
            title="Improve pull request generation",
            summary="Improves generated pull request drafts.",
            why="Makes PR generation more useful.",
            changes=["Improve PR generation."],
            testing=["Run unit tests."],
            risks=[],
            reviewer_focus=[],
            breaking_changes=[],
        )

        mock_pr_service.return_value.generate_draft.return_value = original_draft

        edited_json = '{"title": "Improve pull request generation"}'

        mock_editor.return_value.edit.return_value = edited_json
        mock_parser.return_value.parse.return_value = edited_draft

        mock_view.return_value.prompt_action.side_effect = ["e", "y"]

        result = runner.invoke(app, ["pr"])

        assert result.exit_code == 0

        mock_editor.return_value.edit.assert_called_once()
        mock_parser.return_value.parse.assert_called_once_with(edited_json)

        assert mock_view.return_value.show_generated.call_count == 2

        call = mock_pr_service.return_value.generate_draft.call_args

        assert call.args == ("main",)
        assert "on_attempt" in call.kwargs
        assert callable(call.kwargs["on_attempt"])


def test_pr_regenerates_draft():
    with (
        patch("diffsage.commands.pr.GitClient"),
        patch("diffsage.commands.pr.GitHubClient"),
        patch("diffsage.commands.pr.GitService") as mock_git_service,
        patch("diffsage.commands.pr.GitHubService") as mock_github_service,
        patch("diffsage.commands.pr.PullRequestService") as mock_pr_service,
        patch("diffsage.commands.pr.load_settings"),
        patch("diffsage.commands.pr.AIService"),
        patch("diffsage.commands.pr.get_credentials_path"),
        patch("diffsage.commands.pr.CredentialsRepository"),
        patch("diffsage.commands.pr.CredentialService"),
        patch("diffsage.commands.pr.PullRequestView") as mock_view,
    ):
        mock_git_service.return_value.resolve_base_branch.return_value = "main"
        mock_git_service.return_value.current_branch.return_value = "feature/pr-generation"
        mock_git_service.return_value.validate_remote_head.return_value = None
        mock_github_service.return_value.validate.return_value = None
        mock_github_service.return_value.create_pull_request.return_value = (
            "https://github.com/example/repo/pull/42"
        )

        first_draft = create_pull_request_draft()

        second_draft = PullRequestDraft(
            title="Improve PR generation",
            summary="Improves PR generation.",
            why="Improves generated drafts.",
            changes=["Improve generation."],
            testing=["Run tests."],
            risks=[],
            reviewer_focus=[],
            breaking_changes=[],
        )

        mock_pr_service.return_value.generate_draft.side_effect = [
            first_draft,
            second_draft,
        ]

        mock_view.return_value.prompt_action.side_effect = ["r", "y"]

        result = runner.invoke(app, ["pr"])

        assert result.exit_code == 0

        assert mock_pr_service.return_value.generate_draft.call_count == 2

        for call in mock_pr_service.return_value.generate_draft.call_args_list:
            assert call.args == ("main",)
            assert "on_attempt" in call.kwargs
            assert callable(call.kwargs["on_attempt"])

        assert mock_view.return_value.show_generated.call_count == 2


def test_pr_cancels_draft():
    with (
        patch("diffsage.commands.pr.GitClient"),
        patch("diffsage.commands.pr.GitHubClient"),
        patch("diffsage.commands.pr.GitService") as mock_git_service,
        patch("diffsage.commands.pr.GitHubService"),
        patch("diffsage.commands.pr.PullRequestService") as mock_pr_service,
        patch("diffsage.commands.pr.load_settings"),
        patch("diffsage.commands.pr.AIService"),
        patch("diffsage.commands.pr.get_credentials_path"),
        patch("diffsage.commands.pr.CredentialsRepository"),
        patch("diffsage.commands.pr.CredentialService"),
        patch("diffsage.commands.pr.PullRequestView") as mock_view,
    ):
        mock_git_service.return_value.resolve_base_branch.return_value = "main"

        draft = create_pull_request_draft()
        mock_pr_service.return_value.generate_draft.return_value = draft
        mock_view.return_value.prompt_action.return_value = "n"

        result = runner.invoke(app, ["pr"])

        assert result.exit_code == 0

        call = mock_pr_service.return_value.generate_draft.call_args

        assert call.args == ("main",)
        assert "on_attempt" in call.kwargs
        assert callable(call.kwargs["on_attempt"])

        mock_view.return_value.show_cancelled.assert_called_once()


def test_pr_reprompts_after_invalid_choice():
    with (
        patch("diffsage.commands.pr.GitClient"),
        patch("diffsage.commands.pr.GitHubClient"),
        patch("diffsage.commands.pr.GitService") as mock_git_service,
        patch("diffsage.commands.pr.GitHubService") as mock_github_service,
        patch("diffsage.commands.pr.PullRequestService") as mock_pr_service,
        patch("diffsage.commands.pr.load_settings"),
        patch("diffsage.commands.pr.AIService"),
        patch("diffsage.commands.pr.get_credentials_path"),
        patch("diffsage.commands.pr.CredentialsRepository"),
        patch("diffsage.commands.pr.CredentialService"),
        patch("diffsage.commands.pr.PullRequestView") as mock_view,
    ):
        mock_git_service.return_value.resolve_base_branch.return_value = "main"
        mock_github_service.return_value.create_pull_request.return_value = (
            "https://github.com/example/repo/pull/42"
        )

        draft = create_pull_request_draft()
        mock_pr_service.return_value.generate_draft.return_value = draft
        mock_view.return_value.prompt_action.side_effect = ["x", "y"]

        result = runner.invoke(app, ["pr"])

        assert result.exit_code == 0

        assert mock_view.return_value.prompt_action.call_count == 2
        mock_view.return_value.show_invalid_option.assert_called_once()

        call = mock_pr_service.return_value.generate_draft.call_args

        assert call.args == ("main",)
        assert "on_attempt" in call.kwargs
        assert callable(call.kwargs["on_attempt"])


def test_pr_exits_when_not_in_git_repository():
    with (
        patch("diffsage.commands.pr.GitClient") as mock_git,
        patch("diffsage.commands.pr.PullRequestView") as mock_view,
    ):
        mock_git.side_effect = NotGitRepositoryError("Not a Git repository.")

        with pytest.raises(SystemExit):
            pr()

        mock_view.return_value.show_not_git_repository.assert_called_once()


def test_pr_exits_when_head_is_detached():
    with (
        patch("diffsage.commands.pr.GitClient"),
        patch("diffsage.commands.pr.GitService") as mock_git_service,
        patch("diffsage.commands.pr.load_settings"),
        patch("diffsage.commands.pr.AIService"),
        patch("diffsage.commands.pr.get_credentials_path"),
        patch("diffsage.commands.pr.CredentialsRepository"),
        patch("diffsage.commands.pr.CredentialService"),
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
        patch("diffsage.commands.pr.load_settings"),
        patch("diffsage.commands.pr.AIService"),
        patch("diffsage.commands.pr.get_credentials_path"),
        patch("diffsage.commands.pr.CredentialsRepository"),
        patch("diffsage.commands.pr.CredentialService"),
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
        patch("diffsage.commands.pr.load_settings"),
        patch("diffsage.commands.pr.AIService"),
        patch("diffsage.commands.pr.get_credentials_path"),
        patch("diffsage.commands.pr.CredentialsRepository"),
        patch("diffsage.commands.pr.CredentialService"),
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

        mock_view.return_value.show_error.assert_called_once()


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


def test_pr_handles_invalid_edited_draft():
    with (
        patch("diffsage.commands.pr.GitClient"),
        patch("diffsage.commands.pr.GitHubClient"),
        patch("diffsage.commands.pr.GitService") as mock_git_service,
        patch("diffsage.commands.pr.GitHubService"),
        patch("diffsage.commands.pr.PullRequestService") as mock_pr_service,
        patch("diffsage.commands.pr.load_settings"),
        patch("diffsage.commands.pr.AIService"),
        patch("diffsage.commands.pr.get_credentials_path"),
        patch("diffsage.commands.pr.CredentialsRepository"),
        patch("diffsage.commands.pr.CredentialService"),
        patch("diffsage.commands.pr.EditorService") as mock_editor,
        patch("diffsage.commands.pr.PullRequestParser") as mock_parser,
        patch("diffsage.commands.pr.PullRequestView") as mock_view,
    ):
        mock_git_service.return_value.resolve_base_branch.return_value = "main"

        draft = create_pull_request_draft()

        mock_pr_service.return_value.generate_draft.return_value = draft
        mock_view.return_value.prompt_action.side_effect = ["e", "n"]

        mock_editor.return_value.edit.return_value = "invalid json"

        mock_parser.return_value.parse.side_effect = InvalidPullRequestDraftError(
            "Invalid pull request draft."
        )

        result = runner.invoke(app, ["pr"])

        assert result.exit_code == 0

        mock_parser.return_value.parse.assert_called_once_with("invalid json")
        mock_view.return_value.show_error.assert_called_once_with("Invalid pull request draft.")
        mock_view.return_value.show_cancelled.assert_called_once()


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


def test_pr_exits_when_github_cli_is_unavailable():
    with (
        patch("diffsage.commands.pr.GitClient"),
        patch("diffsage.commands.pr.GitHubClient"),
        patch("diffsage.commands.pr.GitService") as mock_git_service,
        patch("diffsage.commands.pr.GitHubService") as mock_github_service,
        patch("diffsage.commands.pr.PullRequestService") as mock_pr_service,
        patch("diffsage.commands.pr.load_settings"),
        patch("diffsage.commands.pr.AIService"),
        patch("diffsage.commands.pr.get_credentials_path"),
        patch("diffsage.commands.pr.CredentialsRepository"),
        patch("diffsage.commands.pr.CredentialService"),
        patch("diffsage.commands.pr.PullRequestView") as mock_view,
    ):
        mock_git_service.return_value.resolve_base_branch.return_value = "main"

        mock_pr_service.return_value.generate_draft.return_value = create_pull_request_draft()

        mock_view.return_value.prompt_action.return_value = "y"

        mock_github_service.return_value.validate.side_effect = GitHubCLIUnavailableError(
            "GitHub CLI is not installed. Install GitHub CLI and try again."
        )

        result = runner.invoke(app, ["pr"])

        assert result.exit_code == 1

        mock_pr_service.return_value.generate_draft.assert_not_called()
        mock_github_service.return_value.create_pull_request.assert_not_called()
        mock_view.return_value.show_error.assert_called_once_with(
            "GitHub CLI is not installed. Install GitHub CLI and try again."
        )


def test_pr_exits_when_github_cli_is_not_authenticated():
    with (
        patch("diffsage.commands.pr.GitClient"),
        patch("diffsage.commands.pr.GitHubClient"),
        patch("diffsage.commands.pr.GitService") as mock_git_service,
        patch("diffsage.commands.pr.GitHubService") as mock_github_service,
        patch("diffsage.commands.pr.PullRequestService") as mock_pr_service,
        patch("diffsage.commands.pr.load_settings"),
        patch("diffsage.commands.pr.AIService"),
        patch("diffsage.commands.pr.get_credentials_path"),
        patch("diffsage.commands.pr.CredentialsRepository"),
        patch("diffsage.commands.pr.CredentialService"),
        patch("diffsage.commands.pr.PullRequestView") as mock_view,
    ):
        mock_git_service.return_value.resolve_base_branch.return_value = "main"

        mock_pr_service.return_value.generate_draft.return_value = create_pull_request_draft()

        mock_view.return_value.prompt_action.return_value = "y"

        mock_github_service.return_value.validate.side_effect = GitHubAuthenticationError(
            "GitHub CLI is not authenticated. Run 'gh auth login' and try again."
        )

        result = runner.invoke(app, ["pr"])

        assert result.exit_code == 1

        mock_pr_service.return_value.generate_draft.assert_not_called()
        mock_github_service.return_value.create_pull_request.assert_not_called()
        mock_view.return_value.show_error.assert_called_once_with(
            "GitHub CLI is not authenticated. Run 'gh auth login' and try again."
        )


def test_pr_exits_when_remote_branch_does_not_exist():
    with (
        patch("diffsage.commands.pr.GitClient"),
        patch("diffsage.commands.pr.GitHubClient"),
        patch("diffsage.commands.pr.GitService") as mock_git_service,
        patch("diffsage.commands.pr.GitHubService") as mock_github_service,
        patch("diffsage.commands.pr.PullRequestService") as mock_pr_service,
        patch("diffsage.commands.pr.load_settings"),
        patch("diffsage.commands.pr.AIService"),
        patch("diffsage.commands.pr.get_credentials_path"),
        patch("diffsage.commands.pr.CredentialsRepository"),
        patch("diffsage.commands.pr.CredentialService"),
        patch("diffsage.commands.pr.PullRequestView") as mock_view,
    ):
        mock_git_service.return_value.resolve_base_branch.return_value = "main"
        mock_git_service.return_value.current_branch.return_value = "feature/pr-generation"

        mock_git_service.return_value.validate_remote_head.side_effect = RemoteBranchNotFoundError(
            "Remote branch 'feature/pr-generation' does not exist on origin."
        )

        result = runner.invoke(app, ["pr"])

        assert result.exit_code == 1

        mock_git_service.return_value.validate_remote_head.assert_called_once_with(
            "feature/pr-generation"
        )
        mock_pr_service.return_value.generate_draft.assert_not_called()
        mock_github_service.return_value.validate.assert_not_called()
        mock_github_service.return_value.create_pull_request.assert_not_called()
        mock_view.return_value.show_error.assert_called_once()


def test_pr_exits_when_branch_has_unpushed_commits():
    with (
        patch("diffsage.commands.pr.GitClient"),
        patch("diffsage.commands.pr.GitHubClient"),
        patch("diffsage.commands.pr.GitService") as mock_git_service,
        patch("diffsage.commands.pr.GitHubService") as mock_github_service,
        patch("diffsage.commands.pr.PullRequestService") as mock_pr_service,
        patch("diffsage.commands.pr.load_settings"),
        patch("diffsage.commands.pr.AIService"),
        patch("diffsage.commands.pr.get_credentials_path"),
        patch("diffsage.commands.pr.CredentialsRepository"),
        patch("diffsage.commands.pr.CredentialService"),
        patch("diffsage.commands.pr.PullRequestView") as mock_view,
    ):
        mock_git_service.return_value.resolve_base_branch.return_value = "main"
        mock_git_service.return_value.current_branch.return_value = "feature/pr-generation"

        mock_git_service.return_value.validate_remote_head.side_effect = UnpushedChangesError(
            "Local branch 'feature/pr-generation' contains commits "
            "that have not been pushed to origin."
        )

        result = runner.invoke(app, ["pr"])

        assert result.exit_code == 1

        mock_git_service.return_value.validate_remote_head.assert_called_once_with(
            "feature/pr-generation"
        )
        mock_pr_service.return_value.generate_draft.assert_not_called()
        mock_github_service.return_value.validate.assert_not_called()
        mock_github_service.return_value.create_pull_request.assert_not_called()
        mock_view.return_value.show_error.assert_called_once()
