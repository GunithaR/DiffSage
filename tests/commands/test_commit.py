import pytest
from unittest.mock import patch

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
        patch("diffsage.commands.commit.console.input", return_value="y"),
    ):
        git = mock_git.return_value

        git.is_git_repository.return_value = True
        git.staged_diff.return_value = "diff --git"

        service = mock_commit_service.return_value
        service.generate_commit_message.return_value = "feat: add commit command"

        commit()

        service.generate_commit_message.assert_called_once()
        git.commit.assert_called_once_with("feat: add commit command")


def test_commit_cancels_when_user_declines():
    with (
        patch("diffsage.commands.commit.GitClient") as mock_git,
        patch("diffsage.commands.commit.CommitService") as mock_commit_service,
        patch("diffsage.commands.commit.console.input", return_value="n"),
    ):
        git = mock_git.return_value

        git.is_git_repository.return_value = True
        git.staged_diff.return_value = "diff --git"

        service = mock_commit_service.return_value
        service.generate_commit_message.return_value = "feat: add commit command"

        commit()

        service.generate_commit_message.assert_called_once()
        git.commit.assert_not_called()


def test_commit_regenerates_when_user_chooses():
    with (
        patch("diffsage.commands.commit.GitClient") as mock_git,
        patch("diffsage.commands.commit.CommitService") as mock_commit_service,
        patch("diffsage.commands.commit.console.input", side_effect=["r", "y"]),
    ):
        git = mock_git.return_value

        git.is_git_repository.return_value = True
        git.staged_diff.return_value = "diff --git"

        service = mock_commit_service.return_value
        service.generate_commit_message.return_value = "feat: add commit command"

        commit()

        assert service.generate_commit_message.call_count == 2
        git.commit.assert_called_once_with("feat: add commit command")


def test_commit_reprompts_after_invalid_choice():
    with (
        patch("diffsage.commands.commit.GitClient") as mock_git,
        patch("diffsage.commands.commit.CommitService") as mock_commit_service,
        patch("diffsage.commands.commit.console.input", side_effect=["x", "y"]),
    ):
        git = mock_git.return_value

        git.is_git_repository.return_value = True
        git.staged_diff.return_value = "diff --git"

        service = mock_commit_service.return_value
        service.generate_commit_message.return_value = "feat: add commit command"

        commit()

        service.generate_commit_message.assert_called_once()
        git.commit.assert_called_once_with("feat: add commit command")


def test_commit_edit_returns_correct_response():
    with (
        patch("diffsage.commands.commit.GitClient") as mock_git,
        patch("diffsage.commands.commit.CommitService") as mock_commit_service,
        patch("diffsage.commands.commit.EditorService") as mock_editor,
        patch("diffsage.commands.commit.console.input", side_effect=["e", "y"]),
    ):
        git = mock_git.return_value

        git.is_git_repository.return_value = True
        git.staged_diff.return_value = "diff --git"

        service = mock_commit_service.return_value
        service.generate_commit_message.return_value = "feat: add commit command"

        editor = mock_editor.return_value
        editor.edit.return_value = "feat(commit): edited commit message"

        commit()

        service.generate_commit_message.assert_called_once()
        editor.edit.assert_called_once_with("feat: add commit command")
        git.commit.assert_called_once_with("feat(commit): edited commit message")
