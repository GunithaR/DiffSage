from unittest.mock import patch

import pytest

from diffsage.commands.commit import commit


def test_commit_exits_when_not_in_git_repository():
    with patch("diffsage.commands.commit.GitClient") as mock_git:
        git = mock_git.return_value

        git.is_git_repository.return_value = False

        with pytest.raises(SystemExit):
            commit()


def test_commit_exits_when_no_staged_diff_found():
    with patch("diffsage.commands.commit.GitClient") as mock_git:
        git = mock_git.return_value

        git.is_git_repository.return_value = True
        git.staged_diff.return_value = ""

        with pytest.raises(SystemExit):
            commit()


def test_commit_calls_git_commit_on_confirmation():
    with (
        patch("diffsage.commands.commit.GitClient") as mock_git,
        patch("diffsage.commands.commit.CommitService") as mock_commit_service,
        patch("diffsage.commands.commit.load_settings") as mock_load_settings,
        patch("diffsage.commands.commit.AIService") as mock_ai_service,
        patch("diffsage.commands.commit.get_credentials_path") as mock_get_path,
        patch("diffsage.commands.commit.CredentialsRepository") as mock_repository,
        patch("diffsage.commands.commit.CredentialService") as mock_credential_service,
        patch("diffsage.commands.commit.CommitView") as mock_view,
    ):
        git = mock_git.return_value
        settings = mock_load_settings.return_value
        repository = mock_repository.return_value
        credential_service = mock_credential_service.return_value

        git.is_git_repository.return_value = True
        git.staged_diff.return_value = "diff --git"

        service = mock_commit_service.return_value
        service.generate_commit_message.return_value = "feat: add commit command"

        mock_view.return_value.prompt_action.return_value = "y"

        commit()

        call = service.generate_commit_message.call_args

        assert "on_attempt" in call.kwargs
        assert callable(call.kwargs["on_attempt"])

        service.generate_commit_message.assert_called_once()
        git.commit.assert_called_once_with("feat: add commit command")

        mock_get_path.assert_called_once()
        mock_repository.assert_called_once_with(mock_get_path.return_value)
        mock_credential_service.assert_called_once_with(
            repository,
        )
        mock_ai_service.assert_called_once_with(
            settings,
            credential_service,
        )


def test_commit_cancels_when_user_declines():
    with (
        patch("diffsage.commands.commit.GitClient") as mock_git,
        patch("diffsage.commands.commit.CommitService") as mock_commit_service,
        patch("diffsage.commands.commit.load_settings"),
        patch("diffsage.commands.commit.AIService"),
        patch("diffsage.commands.commit.get_credentials_path"),
        patch("diffsage.commands.commit.CredentialsRepository"),
        patch("diffsage.commands.commit.CredentialService"),
        patch("diffsage.commands.commit.CommitView") as mock_view,
    ):
        git = mock_git.return_value

        git.is_git_repository.return_value = True
        git.staged_diff.return_value = "diff --git"

        service = mock_commit_service.return_value
        service.generate_commit_message.return_value = "feat: add commit command"

        mock_view.return_value.prompt_action.return_value = "n"

        commit()

        call = service.generate_commit_message.call_args

        assert "on_attempt" in call.kwargs
        assert callable(call.kwargs["on_attempt"])

        service.generate_commit_message.assert_called_once()
        git.commit.assert_not_called()


def test_commit_regenerates_when_user_chooses():
    with (
        patch("diffsage.commands.commit.GitClient") as mock_git,
        patch("diffsage.commands.commit.CommitService") as mock_commit_service,
        patch("diffsage.commands.commit.load_settings"),
        patch("diffsage.commands.commit.AIService"),
        patch("diffsage.commands.commit.get_credentials_path"),
        patch("diffsage.commands.commit.CredentialsRepository"),
        patch("diffsage.commands.commit.CredentialService"),
        patch("diffsage.commands.commit.CommitView") as mock_view,
    ):
        git = mock_git.return_value

        git.is_git_repository.return_value = True
        git.staged_diff.return_value = "diff --git"

        service = mock_commit_service.return_value
        service.generate_commit_message.return_value = "feat: add commit command"

        mock_view.return_value.prompt_action.side_effect = ["r", "y"]

        commit()

        assert service.generate_commit_message.call_count == 2

        for call in service.generate_commit_message.call_args_list:
            assert callable(call.kwargs["on_attempt"])
        git.commit.assert_called_once_with("feat: add commit command")


def test_commit_reprompts_after_invalid_choice():
    with (
        patch("diffsage.commands.commit.GitClient") as mock_git,
        patch("diffsage.commands.commit.CommitService") as mock_commit_service,
        patch("diffsage.commands.commit.load_settings"),
        patch("diffsage.commands.commit.AIService"),
        patch("diffsage.commands.commit.get_credentials_path"),
        patch("diffsage.commands.commit.CredentialsRepository"),
        patch("diffsage.commands.commit.CredentialService"),
        patch("diffsage.commands.commit.CommitView") as mock_view,
    ):
        git = mock_git.return_value

        git.is_git_repository.return_value = True
        git.staged_diff.return_value = "diff --git"

        service = mock_commit_service.return_value
        service.generate_commit_message.return_value = "feat: add commit command"

        mock_view.return_value.prompt_action.side_effect = ["x", "y"]

        commit()

        call = service.generate_commit_message.call_args

        assert "on_attempt" in call.kwargs
        assert callable(call.kwargs["on_attempt"])

        service.generate_commit_message.assert_called_once()
        git.commit.assert_called_once_with("feat: add commit command")


def test_commit_uses_edited_message():
    with (
        patch("diffsage.commands.commit.GitClient") as mock_git,
        patch("diffsage.commands.commit.CommitService") as mock_commit_service,
        patch("diffsage.commands.commit.EditorService") as mock_editor,
        patch("diffsage.commands.commit.load_settings"),
        patch("diffsage.commands.commit.AIService"),
        patch("diffsage.commands.commit.get_credentials_path"),
        patch("diffsage.commands.commit.CredentialsRepository"),
        patch("diffsage.commands.commit.CredentialService"),
        patch("diffsage.commands.commit.CommitView") as mock_view,
    ):
        git = mock_git.return_value

        git.is_git_repository.return_value = True
        git.staged_diff.return_value = "diff --git"

        service = mock_commit_service.return_value
        service.generate_commit_message.return_value = "feat: add commit command"

        editor = mock_editor.return_value
        editor.edit.return_value = "feat(commit): edited commit message"

        mock_view.return_value.prompt_action.side_effect = ["e", "y"]

        commit()

        call = service.generate_commit_message.call_args

        assert "on_attempt" in call.kwargs
        assert callable(call.kwargs["on_attempt"])

        service.generate_commit_message.assert_called_once()
        editor.edit.assert_called_once_with("feat: add commit command")
        git.commit.assert_called_once_with("feat(commit): edited commit message")
