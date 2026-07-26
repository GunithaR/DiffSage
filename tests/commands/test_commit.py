import pytest
from unittest.mock import patch, call

from diffsage.commands.commit import commit
from diffsage.models.provider import ProviderResponse

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
        patch("diffsage.commands.commit.build_commit_prompt") as mock_prompt,
        patch("diffsage.commands.commit.AIService") as mock_ai,
        patch("diffsage.commands.commit.console.input", return_value="y"),
    ):
        git = mock_git.return_value

        git.is_git_repository.return_value = True
        git.staged_diff.return_value = "diff --git"

        mock_prompt.return_value = "Prompt"
        ai = mock_ai.return_value

        ai.ask.return_value = ProviderResponse(
            content="feat: add commit command",
            provider="gemini",
            model="gemini-3.5-flash-lite",
            input_tokens=100,
            output_tokens=10,
            finish_reason="STOP",
            latency_ms=500,
        )

        commit()

        git.is_git_repository.assert_called_once()
        git.staged_diff.assert_called_once()

        mock_prompt.assert_called_once_with("diff --git")
        ai.ask.assert_called_once_with("Prompt")
        git.commit.assert_called_once_with("feat: add commit command")

def test_commit_cancels_when_user_declines():
    with (
        patch("diffsage.commands.commit.GitClient") as mock_git,
        patch("diffsage.commands.commit.build_commit_prompt") as mock_prompt,
        patch("diffsage.commands.commit.AIService") as mock_ai,
        patch("diffsage.commands.commit.console.input", return_value="n"),
    ):
        git = mock_git.return_value

        git.is_git_repository.return_value = True
        git.staged_diff.return_value = "diff --git"

        mock_prompt.return_value = "Prompt"
        ai = mock_ai.return_value

        ai.ask.return_value = ProviderResponse(
            content="feat: add commit command",
            provider="gemini",
            model="gemini-3.5-flash-lite",
            input_tokens=100,
            output_tokens=10,
            finish_reason="STOP",
            latency_ms=500,
        )

        commit()

        git.is_git_repository.assert_called_once()
        git.staged_diff.assert_called_once()

        mock_prompt.assert_called_once_with("diff --git")
        ai.ask.assert_called_once_with("Prompt")
        git.commit.assert_not_called()

def test_commit_regenerates_when_user_chooses():
    with (
        patch("diffsage.commands.commit.GitClient") as mock_git,
        patch("diffsage.commands.commit.build_commit_prompt") as mock_prompt,
        patch("diffsage.commands.commit.AIService") as mock_ai,
        patch("diffsage.commands.commit.console.input", side_effect=["r", "y"]),
    ):
        git = mock_git.return_value

        git.is_git_repository.return_value = True
        git.staged_diff.return_value = "diff --git"

        mock_prompt.return_value = "Prompt"
        ai = mock_ai.return_value

        ai.ask.side_effect = [
            ProviderResponse(
                content="feat: first message",
                provider="gemini",
                model="gemini-3.5-flash-lite",
                input_tokens=100,
                output_tokens=10,
                finish_reason="STOP",
                latency_ms=500,
            ),
            ProviderResponse(
                content="feat: regenerated message",
                provider="gemini",
                model="gemini-3.5-flash-lite",
                input_tokens=100,
                output_tokens=10,
                finish_reason="STOP",
                latency_ms=500,
            ),
        ]

        commit()

        assert ai.ask.call_count == 2
        assert mock_prompt.call_count == 2
        assert git.is_git_repository.call_count == 2
        assert git.staged_diff.call_count == 2
        assert mock_prompt.call_args_list == [
            call("diff --git"),
            call("diff --git"),
        ]

        git.commit.assert_called_once_with("feat: regenerated message")

def test_commit_reprompts_after_invalid_choice():
    with (
        patch("diffsage.commands.commit.GitClient") as mock_git,
        patch("diffsage.commands.commit.build_commit_prompt") as mock_prompt,
        patch("diffsage.commands.commit.AIService") as mock_ai,
        patch("diffsage.commands.commit.console.input", side_effect=["x", "y"]),
    ):
        git = mock_git.return_value

        git.is_git_repository.return_value = True
        git.staged_diff.return_value = "diff --git"

        mock_prompt.return_value = "Prompt"
        ai = mock_ai.return_value

        ai.ask.return_value = ProviderResponse(
            content="feat: add commit command",
            provider="gemini",
            model="gemini-3.5-flash-lite",
            input_tokens=100,
            output_tokens=10,
            finish_reason="STOP",
            latency_ms=500,
        )

        commit()

        git.is_git_repository.assert_called_once()
        git.staged_diff.assert_called_once()

        mock_prompt.assert_called_once_with("diff --git")
        ai.ask.assert_called_once_with("Prompt")
        git.commit.assert_called_once_with("feat: add commit command")

def test_commit_edit_returns_correct_response():
    with (
        patch("diffsage.commands.commit.GitClient") as mock_git,
        patch("diffsage.commands.commit.build_commit_prompt") as mock_prompt,
        patch("diffsage.commands.commit.AIService") as mock_ai,
        patch("diffsage.commands.commit.EditorService") as mock_editor,
        patch("diffsage.commands.commit.console.input", side_effect=["e", "y"]),
    ):
        git = mock_git.return_value

        git.is_git_repository.return_value = True
        git.staged_diff.return_value = "diff --git"

        mock_prompt.return_value = "Prompt"
        ai = mock_ai.return_value

        editor = mock_editor.return_value
        editor.edit.return_value = "feat(commit): edited commit message"

        ai.ask.return_value = ProviderResponse(
            content="feat: add commit command",
            provider="gemini",
            model="gemini-3.5-flash-lite",
            input_tokens=100,
            output_tokens=10,
            finish_reason="STOP",
            latency_ms=500,
        )

        commit()

        git.is_git_repository.assert_called_once()
        git.staged_diff.assert_called_once()

        mock_prompt.assert_called_once_with("diff --git")
        ai.ask.assert_called_once_with("Prompt")

        editor.edit.assert_called_once_with(
            "feat: add commit command"
        )
        
        git.commit.assert_called_once_with(
            "feat(commit): edited commit message"
        )