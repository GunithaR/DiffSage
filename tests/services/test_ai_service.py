from unittest.mock import Mock, call, patch

import pytest

from diffsage.exceptions import CredentialNotFoundError
from diffsage.exceptions.provider import AuthenticationError, ProviderUnavailableError
from diffsage.models.credentials import Credential
from diffsage.models.provider import ProviderResponse
from diffsage.services.ai_service import AIService
from diffsage.services.credentials_service import CredentialService
from tests.helpers import create_settings


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


def test_ask_does_not_retry_non_retryable_exception():
    provider = Mock()
    credential_service = Mock(spec=CredentialService)

    credential = Credential(
        provider="gemini",
        name="default",
        api_key="test-api-key",
    )

    provider.generate.side_effect = AuthenticationError("Invalid API key")

    settings = create_settings()
    credential_service.get_credential.return_value = credential
    service = AIService(
        settings,
        credential_service,
        provider=provider,
    )

    with patch("diffsage.services.ai_service.time.sleep") as mock_sleep:
        with pytest.raises(AuthenticationError):
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
