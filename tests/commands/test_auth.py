from unittest.mock import patch

import pytest

from diffsage.commands.auth import (
    get_credential,
    list_credentials,
    set_credential,
    unset_credential,
)
from diffsage.exceptions import InvalidCredentialError
from diffsage.models.credentials import Credential
from tests.helpers import assert_error_shown


def test_set_credential_command_orchestrates() -> None:
    with (
        patch("diffsage.commands.auth.get_credentials_path") as mock_get_path,
        patch("diffsage.commands.auth.CredentialsRepository") as mock_repository,
        patch("diffsage.commands.auth.CredentialService") as mock_service,
        patch("diffsage.commands.auth.AuthView") as mock_view,
    ):
        repository = mock_repository.return_value
        service = mock_service.return_value
        view = mock_view.return_value

        set_credential(
            provider=" Gemini ",
            api_key="test-api-key",
            name="default",
        )

    service.set_credential.assert_called_once_with(
        " Gemini ",
        "test-api-key",
        "default",
    )
    mock_get_path.assert_called_once()
    mock_repository.assert_called_once_with(mock_get_path.return_value)
    mock_service.assert_called_once_with(repository)

    view.show_success.assert_called_once()
    view.show_credential.assert_not_called()
    service.get_credential.assert_not_called()


def test_set_credential_command_handles_value_error(capsys) -> None:
    with (
        patch("diffsage.commands.auth.get_credentials_path") as mock_get_path,
        patch("diffsage.commands.auth.CredentialsRepository") as mock_repository,
        patch("diffsage.commands.auth.CredentialService") as mock_service,
        patch("diffsage.commands.auth.AuthView") as mock_view,
    ):
        repository = mock_repository.return_value
        service = mock_service.return_value
        view = mock_view.return_value

        service.set_credential.side_effect = InvalidCredentialError("API cannot be empty.")

        with pytest.raises(SystemExit) as exception_info:
            set_credential(
                provider="gemini",
                api_key="test-api-key",
                name="default",
            )

    assert exception_info.value.code == 1

    mock_get_path.assert_called_once()
    mock_repository.assert_called_once_with(mock_get_path.return_value)
    mock_service.assert_called_once_with(repository)

    service.set_credential.assert_called_once_with(
        "gemini",
        "test-api-key",
        "default",
    )
    assert_error_shown(capsys, "API cannot be empty.")
    view.show_success.assert_not_called()


def test_get_credential_command_uses_default_profile() -> None:
    credential = Credential(
        provider=" Gemini ",
        name="default",
        api_key="test-api-key",
    )

    with (
        patch("diffsage.commands.auth.get_credentials_path") as mock_get_path,
        patch("diffsage.commands.auth.CredentialsRepository") as mock_repository,
        patch("diffsage.commands.auth.CredentialService") as mock_service,
        patch("diffsage.commands.auth.AuthView") as mock_view,
    ):
        repository = mock_repository.return_value
        service = mock_service.return_value
        view = mock_view.return_value

        service.get_credential.return_value = credential

        get_credential(
            provider=" Gemini ",
            name="default",
        )

    mock_get_path.assert_called_once()
    mock_repository.assert_called_once_with(mock_get_path.return_value)
    mock_service.assert_called_once_with(repository)

    service.get_credential.assert_called_once_with(
        " Gemini ",
        "default",
    )
    view.show_credential.assert_called_once_with(credential)


def test_get_credential_command_uses_named_profile() -> None:
    credential = Credential(
        provider="gemini",
        name="paid",
        api_key="test-api-key",
    )

    with (
        patch("diffsage.commands.auth.get_credentials_path") as mock_get_path,
        patch("diffsage.commands.auth.CredentialsRepository") as mock_repository,
        patch("diffsage.commands.auth.CredentialService") as mock_service,
        patch("diffsage.commands.auth.AuthView") as mock_view,
    ):
        repository = mock_repository.return_value
        service = mock_service.return_value
        view = mock_view.return_value

        service.get_credential.return_value = credential

        get_credential(
            provider="gemini",
            name="paid",
        )

    service.get_credential.assert_called_once_with(
        "gemini",
        "paid",
    )
    mock_get_path.assert_called_once()
    mock_repository.assert_called_once_with(mock_get_path.return_value)
    mock_service.assert_called_once_with(repository)
    view.show_credential.assert_called_once_with(credential)


def test_get_credential_command_handles_missing_credential(capsys) -> None:
    with (
        patch("diffsage.commands.auth.get_credentials_path") as mock_get_path,
        patch("diffsage.commands.auth.CredentialsRepository") as mock_repository,
        patch("diffsage.commands.auth.CredentialService") as mock_service,
        patch("diffsage.commands.auth.AuthView") as mock_view,
    ):
        repository = mock_repository.return_value
        service = mock_service.return_value
        view = mock_view.return_value

        service.get_credential.return_value = None

        with pytest.raises(SystemExit) as exception_info:
            get_credential(
                provider="gemini",
                name="default",
            )

    assert exception_info.value.code == 1

    mock_get_path.assert_called_once()
    mock_repository.assert_called_once_with(mock_get_path.return_value)
    mock_service.assert_called_once_with(repository)

    service.get_credential.assert_called_once_with(
        "gemini",
        "default",
    )

    assert_error_shown(capsys, "Credential not found for provider 'gemini' and profile 'default'.")
    view.show_credential.assert_not_called()


def test_get_credential_command_handles_value_error(capsys) -> None:
    with (
        patch("diffsage.commands.auth.get_credentials_path") as mock_get_path,
        patch("diffsage.commands.auth.CredentialsRepository") as mock_repository,
        patch("diffsage.commands.auth.CredentialService") as mock_service,
        patch("diffsage.commands.auth.AuthView") as mock_view,
    ):
        repository = mock_repository.return_value
        service = mock_service.return_value
        view = mock_view.return_value

        service.get_credential.side_effect = InvalidCredentialError("Provider cannot be empty.")

        with pytest.raises(SystemExit) as exception_info:
            get_credential(
                provider="",
                name="default",
            )

    assert exception_info.value.code == 1

    mock_get_path.assert_called_once()
    mock_repository.assert_called_once_with(mock_get_path.return_value)
    mock_service.assert_called_once_with(repository)

    service.get_credential.assert_called_once_with(
        "",
        "default",
    )

    assert_error_shown(capsys, "Provider cannot be empty.")
    view.show_credential.assert_not_called()


def test_get_credential_command_handles_unexpected_error(capsys) -> None:
    with (
        patch("diffsage.commands.auth.get_credentials_path") as mock_get_path,
        patch("diffsage.commands.auth.CredentialsRepository") as mock_repository,
        patch("diffsage.commands.auth.CredentialService") as mock_service,
        patch("diffsage.commands.auth.AuthView") as mock_view,
    ):
        repository = mock_repository.return_value
        service = mock_service.return_value
        view = mock_view.return_value

        service.get_credential.side_effect = RuntimeError("boom")

        with pytest.raises(SystemExit) as exception_info:
            get_credential(
                provider="gemini",
                name="default",
            )

    assert exception_info.value.code == 1

    mock_get_path.assert_called_once()
    mock_repository.assert_called_once_with(mock_get_path.return_value)
    mock_service.assert_called_once_with(repository)

    service.get_credential.assert_called_once_with(
        "gemini",
        "default",
    )

    assert_error_shown(
        capsys, "An unexpected error occurred. Please check the log file for more details."
    )
    view.show_credential.assert_not_called()


def test_list_credentials_command_orchestrates() -> None:
    credentials = [
        Credential(
            provider="gemini",
            name="default",
            api_key="gemini-key",
        ),
        Credential(
            provider="openai",
            name="default",
            api_key="openai-key",
        ),
    ]

    with (
        patch("diffsage.commands.auth.get_credentials_path") as mock_get_path,
        patch("diffsage.commands.auth.CredentialsRepository") as mock_repository,
        patch("diffsage.commands.auth.CredentialService") as mock_service,
        patch("diffsage.commands.auth.AuthView") as mock_view,
    ):
        repository = mock_repository.return_value
        service = mock_service.return_value
        view = mock_view.return_value

        service.list_credentials.return_value = credentials

        list_credentials()

    mock_get_path.assert_called_once()
    mock_repository.assert_called_once_with(mock_get_path.return_value)
    mock_service.assert_called_once_with(repository)

    service.list_credentials.assert_called_once_with()
    view.show_credentials.assert_called_once_with(credentials)


def test_list_credentials_command_handles_empty_list() -> None:
    with (
        patch("diffsage.commands.auth.get_credentials_path") as mock_get_path,
        patch("diffsage.commands.auth.CredentialsRepository") as mock_repository,
        patch("diffsage.commands.auth.CredentialService") as mock_service,
        patch("diffsage.commands.auth.AuthView") as mock_view,
    ):
        repository = mock_repository.return_value
        service = mock_service.return_value
        view = mock_view.return_value

        service.list_credentials.return_value = []

        list_credentials()

    mock_get_path.assert_called_once()
    mock_repository.assert_called_once_with(mock_get_path.return_value)
    mock_service.assert_called_once_with(repository)

    service.list_credentials.assert_called_once_with()
    view.show_credentials.assert_called_once_with([])
    view.show_error.assert_not_called()


def test_unset_credential_command_uses_default_profile() -> None:
    with (
        patch("diffsage.commands.auth.get_credentials_path") as mock_get_path,
        patch("diffsage.commands.auth.CredentialsRepository") as mock_repository,
        patch("diffsage.commands.auth.CredentialService") as mock_service,
        patch("diffsage.commands.auth.AuthView") as mock_view,
    ):
        repository = mock_repository.return_value
        service = mock_service.return_value
        view = mock_view.return_value

        unset_credential(
            provider=" Gemini ",
            name="default",
        )

    mock_get_path.assert_called_once()
    mock_repository.assert_called_once_with(mock_get_path.return_value)
    mock_service.assert_called_once_with(repository)

    service.delete_credential.assert_called_once_with(
        " Gemini ",
        "default",
    )
    view.show_success.assert_called_once_with("Credential removed.")


def test_unset_credential_command_uses_named_profile() -> None:
    with (
        patch("diffsage.commands.auth.get_credentials_path") as mock_get_path,
        patch("diffsage.commands.auth.CredentialsRepository") as mock_repository,
        patch("diffsage.commands.auth.CredentialService") as mock_service,
        patch("diffsage.commands.auth.AuthView") as mock_view,
    ):
        repository = mock_repository.return_value
        service = mock_service.return_value
        view = mock_view.return_value

        unset_credential(
            provider="gemini",
            name="paid",
        )

    service.delete_credential.assert_called_once_with(
        "gemini",
        "paid",
    )
    mock_get_path.assert_called_once()
    mock_repository.assert_called_once_with(mock_get_path.return_value)
    mock_service.assert_called_once_with(repository)
    view.show_success.assert_called_once_with("Credential removed.")


def test_unset_credential_command_handles_missing_credential(capsys) -> None:
    with (
        patch("diffsage.commands.auth.get_credentials_path") as mock_get_path,
        patch("diffsage.commands.auth.CredentialsRepository") as mock_repository,
        patch("diffsage.commands.auth.CredentialService") as mock_service,
        patch("diffsage.commands.auth.AuthView") as mock_view,
    ):
        repository = mock_repository.return_value
        service = mock_service.return_value
        view = mock_view.return_value

        service.delete_credential.return_value = False

        with pytest.raises(SystemExit) as exception_info:
            unset_credential(
                provider="gemini",
                name="default",
            )

    assert exception_info.value.code == 1

    mock_get_path.assert_called_once()
    mock_repository.assert_called_once_with(mock_get_path.return_value)
    mock_service.assert_called_once_with(repository)

    service.delete_credential.assert_called_once_with(
        "gemini",
        "default",
    )

    assert_error_shown(capsys, "Credential not found for provider 'gemini' and profile 'default'.")
    view.show_success.assert_not_called()


def test_unset_credential_command_handles_value_error(capsys) -> None:
    with (
        patch("diffsage.commands.auth.get_credentials_path") as mock_get_path,
        patch("diffsage.commands.auth.CredentialsRepository") as mock_repository,
        patch("diffsage.commands.auth.CredentialService") as mock_service,
        patch("diffsage.commands.auth.AuthView") as mock_view,
    ):
        repository = mock_repository.return_value
        service = mock_service.return_value
        view = mock_view.return_value

        service.delete_credential.side_effect = InvalidCredentialError(
            "Credential profile name cannot be empty."
        )

        with pytest.raises(SystemExit) as exception_info:
            unset_credential(
                provider="gemini",
                name="",
            )

    assert exception_info.value.code == 1

    mock_get_path.assert_called_once()
    mock_repository.assert_called_once_with(mock_get_path.return_value)
    mock_service.assert_called_once_with(repository)

    service.delete_credential.assert_called_once_with(
        "gemini",
        "",
    )

    assert_error_shown(capsys, "Credential profile name cannot be empty.")
    view.show_success.assert_not_called()


def test_unset_credential_command_handles_unexpected_error(capsys) -> None:
    with (
        patch("diffsage.commands.auth.get_credentials_path") as mock_get_path,
        patch("diffsage.commands.auth.CredentialsRepository") as mock_repository,
        patch("diffsage.commands.auth.CredentialService") as mock_service,
        patch("diffsage.commands.auth.AuthView") as mock_view,
    ):
        repository = mock_repository.return_value
        service = mock_service.return_value
        view = mock_view.return_value

        service.delete_credential.side_effect = RuntimeError("boom")

        with pytest.raises(SystemExit) as exception_info:
            unset_credential(
                provider="gemini",
                name="default",
            )

    assert exception_info.value.code == 1

    mock_get_path.assert_called_once()
    mock_repository.assert_called_once_with(mock_get_path.return_value)
    mock_service.assert_called_once_with(repository)

    service.delete_credential.assert_called_once_with(
        "gemini",
        "default",
    )

    assert_error_shown(
        capsys, "An unexpected error occurred. Please check the log file for more details."
    )
    view.show_success.assert_not_called()
