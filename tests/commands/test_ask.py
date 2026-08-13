from unittest.mock import patch

import pytest

from diffsage.commands.ask import ask
from diffsage.exceptions import (
    AuthenticationError,
    ConfigError,
    ModelNotFoundError,
    ProviderUnavailableError,
)
from diffsage.models.provider import ProviderResponse


def test_ask_command_orchestrates() -> None:
    response = ProviderResponse(
        content="Hello from Gemini",
        provider="gemini",
        model="gemini-3.5-flash-lite",
        input_tokens=10,
        output_tokens=20,
        finish_reason="STOP",
        latency_ms=100,
    )

    with (
        patch("diffsage.commands.ask.load_settings") as mock_load_settings,
        patch("diffsage.commands.ask.get_credentials_path") as mock_get_path,
        patch("diffsage.commands.ask.CredentialsRepository") as mock_repository,
        patch("diffsage.commands.ask.CredentialService") as mock_credential_service,
        patch("diffsage.commands.ask.AIService") as mock_ai_service,
        patch("diffsage.commands.ask.AskView") as mock_view,
    ):
        settings = mock_load_settings.return_value
        path = mock_get_path.return_value
        repository = mock_repository.return_value
        credential_service = mock_credential_service.return_value
        service = mock_ai_service.return_value
        view = mock_view.return_value

        service.ask.return_value = response

        ask("Hello")

    mock_load_settings.assert_called_once()

    mock_get_path.assert_called_once()

    mock_repository.assert_called_once_with(path)

    mock_credential_service.assert_called_once_with(repository)

    mock_ai_service.assert_called_once_with(
        settings,
        credential_service,
    )

    service.ask.assert_called_once_with("Hello")
    view.show_response.assert_called_once_with(response)


def test_ask_command_handles_authentication_error() -> None:
    with (
        patch("diffsage.commands.ask.load_settings"),
        patch("diffsage.commands.ask.get_credentials_path"),
        patch("diffsage.commands.ask.CredentialsRepository"),
        patch("diffsage.commands.ask.CredentialService"),
        patch("diffsage.commands.ask.AIService") as mock_ai_service,
        patch("diffsage.commands.ask.AskView") as mock_view,
    ):
        service = mock_ai_service.return_value
        view = mock_view.return_value

        service.ask.side_effect = AuthenticationError("Invalid API key")

        with pytest.raises(SystemExit) as exception_info:
            ask("Hello")

    assert exception_info.value.code == 1

    service.ask.assert_called_once_with("Hello")
    view.show_error.assert_called_once_with("Invalid API key")
    view.show_response.assert_not_called()


def test_ask_command_handles_model_not_found_error() -> None:
    with (
        patch("diffsage.commands.ask.load_settings"),
        patch("diffsage.commands.ask.get_credentials_path"),
        patch("diffsage.commands.ask.CredentialsRepository"),
        patch("diffsage.commands.ask.CredentialService"),
        patch("diffsage.commands.ask.AIService") as mock_ai_service,
        patch("diffsage.commands.ask.AskView") as mock_view,
    ):
        service = mock_ai_service.return_value
        view = mock_view.return_value

        service.ask.side_effect = ModelNotFoundError("Model 'gemini-3.5-flash-lit' was not found.")

        with pytest.raises(SystemExit) as exception_info:
            ask("Hello")

    assert exception_info.value.code == 1

    service.ask.assert_called_once_with("Hello")
    view.show_error.assert_called_once_with("Model 'gemini-3.5-flash-lit' was not found.")
    view.show_reponse.assert_not_called()


def test_ask_command_handles_provider_unavailable_error() -> None:
    with (
        patch("diffsage.commands.ask.load_settings"),
        patch("diffsage.commands.ask.get_credentials_path"),
        patch("diffsage.commands.ask.CredentialsRepository"),
        patch("diffsage.commands.ask.CredentialService"),
        patch("diffsage.commands.ask.AIService") as mock_ai_service,
        patch("diffsage.commands.ask.AskView") as mock_view,
    ):
        service = mock_ai_service.return_value
        view = mock_view.return_value

        service.ask.side_effect = ProviderUnavailableError("Provider temporarily unavailable.")

        with pytest.raises(SystemExit) as exception_info:
            ask("Hello")

    assert exception_info.value.code == 1

    service.ask.assert_called_once_with("Hello")
    view.show_error.assert_called_once_with("Provider temporarily unavailable.")
    view.show_response.assert_not_called()


def test_ask_command_handles_config_error() -> None:
    with (
        patch("diffsage.commands.ask.load_settings"),
        patch("diffsage.commands.ask.get_credentials_path"),
        patch("diffsage.commands.ask.CredentialsRepository"),
        patch("diffsage.commands.ask.CredentialService"),
        patch("diffsage.commands.ask.AIService") as mock_ai_service,
        patch("diffsage.commands.ask.AskView") as mock_view,
    ):
        service = mock_ai_service.return_value
        view = mock_view.return_value

        service.ask.side_effect = ConfigError("Invalid configuration.")

        with pytest.raises(SystemExit) as exception_info:
            ask("Hello")

    assert exception_info.value.code == 1

    service.ask.assert_called_once_with("Hello")
    view.show_error.assert_called_once_with("Invalid configuration.")
    view.show_response.assert_not_called()


def test_ask_command_handles_unexpected_error() -> None:
    with (
        patch("diffsage.commands.ask.load_settings"),
        patch("diffsage.commands.ask.get_credentials_path"),
        patch("diffsage.commands.ask.CredentialsRepository"),
        patch("diffsage.commands.ask.CredentialService"),
        patch("diffsage.commands.ask.AIService") as mock_ai_service,
        patch("diffsage.commands.ask.AskView") as mock_view,
    ):
        service = mock_ai_service.return_value
        view = mock_view.return_value

        service.ask.side_effect = RuntimeError("boom")

        with pytest.raises(SystemExit) as exception_info:
            ask("Hello")

    assert exception_info.value.code == 1

    service.ask.assert_called_once_with("Hello")
    view.show_error.assert_called_once_with(
        "An unexpected error occurred. Please check the log file for more details."
    )
    view.show_response.assert_not_called()
