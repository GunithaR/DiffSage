from unittest.mock import Mock

from diffsage.models.git import CommitContext
from diffsage.models.provider import ProviderResponse
from diffsage.services.commit_service import CommitService


def test_generate_commit_message_forwards_attempt_callback() -> None:
    git_client = Mock()
    git_service = Mock()
    prompt_service = Mock()
    ai_service = Mock()

    git_service.build_commit_context.return_value = CommitContext(
        branch="main", staged_diff="", unstaged_diff="", recent_commits=[]
    )
    prompt_service.build_commit_prompt.return_value = "prompt"

    ai_service.ask.return_value = ProviderResponse(
        content='{"message": "feat: add retry progress"}',
        provider="test-provider",
        model="test-model",
        input_tokens=10,
        output_tokens=20,
        finish_reason="stop",
        latency_ms=100,
    )

    service = CommitService(
        git_client,
        git_service,
        prompt_service,
        ai_service,
    )

    on_attempt = Mock()

    result = service.generate_commit_message(
        on_attempt=on_attempt,
    )

    assert result == '{"message": "feat: add retry progress"}'

    ai_service.ask.assert_called_once_with(
        "prompt",
        on_attempt=on_attempt,
    )


def test_generate_commit_message_without_attempt_callback() -> None:
    git_client = Mock()
    git_service = Mock()
    prompt_service = Mock()
    ai_service = Mock()

    git_service.build_commit_context.return_value = CommitContext(
        branch="main", staged_diff="", unstaged_diff="", recent_commits=[]
    )
    prompt_service.build_commit_prompt.return_value = "prompt"

    ai_service.ask.return_value = ProviderResponse(
        content='{"message": "feat: add retry progress"}',
        provider="test-provider",
        model="test-model",
        input_tokens=10,
        output_tokens=20,
        finish_reason="stop",
        latency_ms=100,
    )

    service = CommitService(
        git_client,
        git_service,
        prompt_service,
        ai_service,
    )

    result = service.generate_commit_message()

    assert result == '{"message": "feat: add retry progress"}'

    ai_service.ask.assert_called_once_with(
        "prompt",
        on_attempt=None,
    )
