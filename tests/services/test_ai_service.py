import pytest

from unittest.mock import Mock, patch, call

from diffsage.config.settings import Settings
from diffsage.exceptions.provider import AuthenticationError ,ProviderUnavailableError
from diffsage.models.provider import ProviderResponse
from diffsage.services.ai_service import AIService
from tests.helpers import create_settings


def test_ask_returns_response_on_first_attempt():
    provider = Mock()

    response = ProviderResponse(
        content="feat: add retry logic",
        provider="gemini",
        model="test-model",
        input_tokens=10,
        output_tokens=10,
        finish_reason="stop",
        latency_ms=300
    )

    settings = create_settings()
    provider.generate.return_value = response
    service = AIService(settings, provider=provider)
    result = service.ask("prompt")

    assert result == response
    provider.generate.assert_called_once()
    

def test_ask_retries_once_then_returns_response():
    provider = Mock()

    response = ProviderResponse(
            content="feat: add retry logic",
            provider="gemini",
            model="test-model",
            input_tokens=10,
            output_tokens=10,
            finish_reason="stop",
            latency_ms=300
    )

    provider.generate.side_effect = [
            ProviderUnavailableError("Temporary failure"),
            response,
    ]

    settings = create_settings()
    service = AIService(settings, provider=provider)

    with patch("diffsage.services.ai_service.time.sleep") as mock_sleep:
        result = service.ask("prompt")

    assert result == response
    assert provider.generate.call_count == 2
    mock_sleep.assert_called_once_with(1)


def test_ask_retries_multiple_times_then_returns_response():
    provider = Mock()
    
    response = ProviderResponse(
            content="feat: add retry logic",
            provider="gemini",
            model="test-model",
            input_tokens=10,
            output_tokens=10,
            finish_reason="stop",
            latency_ms=300
    )

    provider.generate.side_effect = [
            ProviderUnavailableError("1"),
            ProviderUnavailableError("2"),
            response,
    ]

    settings = create_settings()
    service = AIService(settings, provider=provider)

    with patch("diffsage.services.ai_service.time.sleep") as mock_sleep:
        result = service.ask("prompt")

    assert result == response
    assert provider.generate.call_count == 3
    mock_sleep.assert_has_calls([
        call(1),
        call(2),
    ])

def test_ask_raises_after_exhausting_retries():
    provider = Mock()

    provider.generate.side_effect = [
            ProviderUnavailableError("1"),
            ProviderUnavailableError("2"),
            ProviderUnavailableError("3"),
            ProviderUnavailableError("4"),
    ]

    settings = create_settings()
    service = AIService(settings, provider=provider)

    with patch("diffsage.services.ai_service.time.sleep") as mock_sleep:
        with pytest.raises(ProviderUnavailableError):
            service.ask("prompt")

    assert provider.generate.call_count == settings.max_retries + 1

    mock_sleep.assert_has_calls([
        call(1),
        call(2),
        call(4),
    ])


def test_ask_does_not_retry_non_retryable_exception():
    provider = Mock()

    provider.generate.side_effect = AuthenticationError("Invalid API key")

    settings = create_settings()
    service = AIService(settings, provider=provider)

    with patch("diffsage.services.ai_service.time.sleep") as mock_sleep:
        with pytest.raises(AuthenticationError):
            service.ask("prompt")

    assert provider.generate.call_count == 1
    mock_sleep.assert_not_called()
