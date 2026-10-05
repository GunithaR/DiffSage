import random
from unittest.mock import Mock, call, patch

import pytest

from diffsage.exceptions import CredentialNotFoundError
from diffsage.exceptions.provider import (
    AuthenticationError,
    ContentBlockedError,
    EmptyResponseError,
    ProviderUnavailableError,
    RateLimitError,
    ResponseTruncatedError,
)
from diffsage.models.credentials import Credential
from diffsage.models.provider import ProviderResponse
from diffsage.services.ai_service import (
    MAX_BACKOFF_SECONDS,
    MAX_SUGGESTED_WAIT_SECONDS,
    AIService,
)
from diffsage.services.credentials_service import CredentialService
from tests.helpers import create_settings

REAL_UNIFORM = random.uniform


@pytest.fixture(autouse=True)
def no_jitter(monkeypatch):
    """Always pick the full backoff step, so delays are predictable (1s, 2s, 4s, ...)."""

    monkeypatch.setattr("diffsage.services.ai_service.random.uniform", lambda _low, high: high)


def test_ask_returns_response_on_first_attempt():
    provider = Mock()
    credential_service = Mock(spec=CredentialService)

    credential = Credential(
        provider="gemini",
        name="default",
        api_key="test-api-key",
    )

    response = ProviderResponse(
        content="feat: add retry logic",
        provider="gemini",
        model="test-model",
        input_tokens=10,
        output_tokens=10,
        finish_reason="stop",
        latency_ms=300,
    )

    settings = create_settings()
    provider.generate.return_value = response
    credential_service.get_credential.return_value = credential
    service = AIService(
        settings=settings,
        credential_service=credential_service,
        provider=provider,
    )
    result = service.ask("prompt")

    assert result == response
    credential_service.get_credential.assert_not_called()
    provider.generate.assert_called_once()


def test_ask_retries_once_then_returns_response():
    provider = Mock()
    credential_service = Mock(spec=CredentialService)

    credential = Credential(
        provider="gemini",
        name="default",
        api_key="test-api-key",
    )

    response = ProviderResponse(
        content="feat: add retry logic",
        provider="gemini",
        model="test-model",
        input_tokens=10,
        output_tokens=10,
        finish_reason="stop",
        latency_ms=300,
    )

    provider.generate.side_effect = [
        ProviderUnavailableError("Temporary failure"),
        response,
    ]

    settings = create_settings()
    credential_service.get_credential.return_value = credential
    service = AIService(
        settings,
        credential_service,
        provider=provider,
    )

    with patch("diffsage.services.ai_service.time.sleep") as mock_sleep:
        result = service.ask("prompt")

    assert result == response
    assert provider.generate.call_count == 2
    mock_sleep.assert_called_once_with(1)


def test_ask_retries_multiple_times_then_returns_response():
    provider = Mock()
    credential_service = Mock(spec=CredentialService)

    credential = Credential(
        provider="gemini",
        name="default",
        api_key="test-api-key",
    )

    response = ProviderResponse(
        content="feat: add retry logic",
        provider="gemini",
        model="test-model",
        input_tokens=10,
        output_tokens=10,
        finish_reason="stop",
        latency_ms=300,
    )

    provider.generate.side_effect = [
        ProviderUnavailableError("1"),
        ProviderUnavailableError("2"),
        response,
    ]

    settings = create_settings()
    credential_service.get_credential.return_value = credential
    service = AIService(
        settings,
        credential_service,
        provider=provider,
    )

    with patch("diffsage.services.ai_service.time.sleep") as mock_sleep:
        result = service.ask("prompt")

    assert result == response
    assert provider.generate.call_count == 3
    mock_sleep.assert_has_calls(
        [
            call(1),
            call(2),
        ]
    )


def test_ask_raises_after_exhausting_retries():
    provider = Mock()
    credential_service = Mock(spec=CredentialService)

    credential = Credential(
        provider="gemini",
        name="default",
        api_key="test-api-key",
    )

    provider.generate.side_effect = [
        ProviderUnavailableError("1"),
        ProviderUnavailableError("2"),
        ProviderUnavailableError("3"),
        ProviderUnavailableError("4"),
    ]

    settings = create_settings()
    credential_service.get_credential.return_value = credential
    service = AIService(
        settings,
        credential_service,
        provider=provider,
    )

    with patch("diffsage.services.ai_service.time.sleep") as mock_sleep:
        with pytest.raises(ProviderUnavailableError):
            service.ask("prompt")

    assert provider.generate.call_count == settings.max_retries + 1

    mock_sleep.assert_has_calls(
        [
            call(1),
            call(2),
            call(4),
        ]
    )


@pytest.mark.parametrize(
    "error",
    [
        AuthenticationError("Invalid API key"),
        ResponseTruncatedError("cut off"),
        ContentBlockedError("blocked"),
        EmptyResponseError(),
    ],
)
def test_ask_does_not_retry_non_retryable_exception(error):
    provider = Mock()
    credential_service = Mock(spec=CredentialService)

    credential = Credential(
        provider="gemini",
        name="default",
        api_key="test-api-key",
    )

    provider.generate.side_effect = error

    settings = create_settings()
    credential_service.get_credential.return_value = credential
    service = AIService(
        settings,
        credential_service,
        provider=provider,
    )

    with patch("diffsage.services.ai_service.time.sleep") as mock_sleep:
        with pytest.raises(type(error)):
            service.ask("prompt")

    assert provider.generate.call_count == 1
    mock_sleep.assert_not_called()


def test_ai_service_resolves_default_credential():
    credential_service = Mock(spec=CredentialService)

    credential = Credential(
        provider="gemini",
        name="default",
        api_key="test-api-key",
    )

    credential_service.resolve_credential.return_value = credential

    settings = create_settings()

    provider = Mock()

    with patch(
        "diffsage.services.ai_service.create_provider",
        return_value=provider,
    ) as mock_create_provider:
        service = AIService(
            settings=settings,
            credential_service=credential_service,
        )

    credential_service.resolve_credential.assert_called_once_with(
        "gemini",
        "default",
    )

    mock_create_provider.assert_called_once_with(
        settings,
        credential,
    )

    assert service._provider is provider


def test_ai_service_raises_when_credential_is_missing():
    credential_service = Mock(spec=CredentialService)
    credential_service.resolve_credential.side_effect = CredentialNotFoundError("gemini")

    settings = create_settings()

    with pytest.raises(
        CredentialNotFoundError,
        match="Credential not found for provider 'gemini' and profile 'default'.",
    ):
        AIService(
            settings=settings,
            credential_service=credential_service,
        )

    credential_service.resolve_credential.assert_called_once_with(
        "gemini",
        "default",
    )


def test_ai_service_resolves_the_configured_credential_profile():
    credential_service = Mock(spec=CredentialService)
    credential_service.resolve_credential.return_value = Credential("gemini", "paid", "paid-key")

    with patch("diffsage.services.ai_service.create_provider"):
        AIService(
            settings=create_settings(credential_profile="paid"),
            credential_service=credential_service,
        )

    credential_service.resolve_credential.assert_called_once_with("gemini", "paid")


def service_with_provider(provider: Mock) -> AIService:
    return AIService(create_settings(), Mock(spec=CredentialService), provider=provider)


def ok_response() -> ProviderResponse:
    return ProviderResponse(
        content="ok",
        provider="gemini",
        model="test-model",
        input_tokens=1,
        output_tokens=1,
        finish_reason="STOP",
        latency_ms=1,
    )


def test_ask_retries_a_rate_limit_with_backoff():
    """Regression: a 429 failed the command at once, although waiting usually fixes it."""

    provider = Mock()
    provider.generate.side_effect = [RateLimitError(), RateLimitError(), ok_response()]

    with patch("diffsage.services.ai_service.time.sleep") as mock_sleep:
        result = service_with_provider(provider).ask("prompt")

    assert result.content == "ok"
    assert provider.generate.call_count == 3
    assert mock_sleep.call_args_list == [call(1), call(2)]


def test_ask_waits_as_long_as_the_provider_asks():
    provider = Mock()
    provider.generate.side_effect = [RateLimitError(retry_after=7.5), ok_response()]

    with patch("diffsage.services.ai_service.time.sleep") as mock_sleep:
        service_with_provider(provider).ask("prompt")

    mock_sleep.assert_called_once_with(7.5)


def test_ask_does_not_retry_when_the_provider_asks_for_a_long_wait():
    """A daily quota asks for hours; retrying would only hang the command."""

    error = RateLimitError("limit", retry_after=MAX_SUGGESTED_WAIT_SECONDS + 1)
    provider = Mock()
    provider.generate.side_effect = [error, ok_response()]

    with patch("diffsage.services.ai_service.time.sleep") as mock_sleep:
        with pytest.raises(RateLimitError) as raised:
            service_with_provider(provider).ask("prompt")

    assert raised.value is error
    assert provider.generate.call_count == 1
    mock_sleep.assert_not_called()


def test_ask_raises_the_last_rate_limit_after_exhausting_retries():
    errors = [RateLimitError(str(number)) for number in range(4)]
    provider = Mock()
    provider.generate.side_effect = errors

    with pytest.raises(RateLimitError) as raised:
        service_with_provider(provider).ask("prompt")

    assert raised.value is errors[-1]
    assert provider.generate.call_count == create_settings().max_retries + 1


@pytest.mark.parametrize(
    ("attempt", "step"), [(0, 1), (1, 2), (3, 8), (4, 16), (5, MAX_BACKOFF_SECONDS), (10, 30)]
)
def test_backoff_is_jittered_between_half_and_the_whole_step(monkeypatch, attempt, step):
    monkeypatch.setattr("diffsage.services.ai_service.random.uniform", REAL_UNIFORM)
    service = service_with_provider(Mock())

    delays = {service._backoff_delay(attempt) for _ in range(50)}

    assert all(step / 2 <= delay <= step for delay in delays)
    assert len(delays) > 1
