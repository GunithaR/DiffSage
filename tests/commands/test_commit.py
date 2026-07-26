import pytest
from unittest.mock import patch

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
