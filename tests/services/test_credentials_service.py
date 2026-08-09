from unittest.mock import Mock

import pytest

from diffsage.models.credentials import Credential
from diffsage.services.credentials_service import CredentialService
from diffsage.storage.credentials_repository import CredentialsRepository


def test_set_credential_saves_default_profile() -> None:
    repository = Mock(spec=CredentialsRepository)
    service = CredentialService(repository)

    service.set_credential(
        provider="gemini",
        api_key="test-api-key",
    )

    repository.save.assert_called_once_with(
        Credential(
            provider="gemini",
            name="default",
            api_key="test-api-key",
        )
    )

def test_set_credential_saves_named_profile() -> None:
    repository = Mock(spec=CredentialsRepository)
    service = CredentialService(repository)

    service.set_credential(
        provider="gemini",
        api_key="paid-api-key",
        name="paid",
    )

    repository.save.assert_called_once_with(
        Credential(
            provider="gemini",
            name="paid",
            api_key="paid-api-key",
        )
    )

def test_set_credential_normalizes_provider_and_name() -> None:
    repository = Mock(spec=CredentialsRepository)
    service = CredentialService(repository)

    service.set_credential(
        provider=" Gemini ",
        api_key="test-api-key",
        name=" Paid ",
    )

    repository.save.assert_called_once_with(
        Credential(
            provider="gemini",
            name="paid",
            api_key="test-api-key",
        )
    )

def test_set_credential_strips_api_key_whitespace() -> None:
    repository = Mock(spec=CredentialsRepository)
    service = CredentialService(repository)

    service.set_credential(
        provider="gemini",
        api_key="  test-api-key  ",
    )

    repository.save.assert_called_once_with(
        Credential(
            provider="gemini",
            name="default",
            api_key="test-api-key",
        )
    )

def test_set_credential_rejects_empty_provider() -> None:
    repository = Mock(spec=CredentialsRepository)
    service = CredentialService(repository)

    with pytest.raises(ValueError):
        service.set_credential(
            provider="   ",
            api_key="test-api-key",
        )

    repository.save.assert_not_called()

def test_set_credential_rejects_empty_profile_name() -> None:
    repository = Mock(spec=CredentialsRepository)
    service = CredentialService(repository)

    with pytest.raises(ValueError):
        service.set_credential(
            provider="gemini",
            api_key="test-api-key",
            name="   ",
        )

    repository.save.assert_not_called()

def test_set_credential_rejects_empty_api_key() -> None:
    repository = Mock(spec=CredentialsRepository)
    service = CredentialService(repository)

    with pytest.raises(ValueError):
        service.set_credential(
            provider="gemini",
            api_key="   ",
        )

    repository.save.assert_not_called()

def test_get_credential_returns_existing_credential() -> None:
    repository = Mock(spec=CredentialsRepository)

    credential = Credential(
        provider="gemini",
        name="default",
        api_key="test-api-key",
    )

    repository.get.return_value = credential
    service = CredentialService(repository)

    result = service.get_credential(" Gemini ")

    repository.get.assert_called_once_with("gemini", "default")
    assert result == credential

def test_get_credential_returns_named_profile() -> None:
    repository = Mock(spec=CredentialsRepository)

    credential = Credential(
        provider="gemini",
        name="paid",
        api_key="paid-key",
    )

    repository.get.return_value = credential

    service = CredentialService(repository)

    result = service.get_credential(
        provider=" Gemini ",
        name=" Paid ",
    )

    repository.get.assert_called_once_with("gemini", "paid")
    assert result == credential

def test_get_credential_returns_none_when_not_found() -> None:
    repository = Mock(spec=CredentialsRepository)
    repository.get.return_value = None

    service = CredentialService(repository)
    
    result = service.get_credential("gemini")

    assert result is None

def test_get_credential_rejects_empty_provider() -> None:
    repository = Mock(spec=CredentialsRepository)
    service = CredentialService(repository)

    with pytest.raises(ValueError):
        service.get_credential(provider=" ")

    repository.get.assert_not_called()

def test_get_credential_rejects_empty_profile_name() -> None:
    repository = Mock(spec=CredentialsRepository)
    service = CredentialService(repository)

    with pytest.raises(ValueError):
        service.get_credential(
            provider="gemini",
            name="  ",
        )

    repository.get.assert_not_called()

def test_list_credentials_return_all_credentials() -> None:
    repository = Mock(spec=CredentialsRepository)

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

    repository.list.return_value = credentials

    service = CredentialService(repository)

    result = service.list_credentials()

    repository.list.assert_called_once()
    assert result == credentials

def test_list_credentials_returns_empty_list_when_no_credentials() -> None:
    repository = Mock(spec=CredentialsRepository)
    repository.list.return_value = []

    service = CredentialService(repository)

    result = service.list_credentials()

    repository.list.assert_called_once()
    assert result == []

def test_delete_credential_deletes_default_profile() -> None:
    repository = Mock(spec=CredentialsRepository)
    service = CredentialService(repository)

    service.delete_credential(" gemini ")

    repository.delete.assert_called_once_with("gemini", "default")

def test_delete_credential_deletes_named_profile() -> None:
    repository = Mock(spec=CredentialsRepository)
    service = CredentialService(repository)

    service.delete_credential(
        provider=" Gemini ",
        name=" Paid ",
    )

    repository.delete.assert_called_once_with("gemini", "paid")

def test_delete_credential_rejects_empty_provider() -> None:
    repository = Mock(spec=CredentialsRepository)
    service = CredentialService(repository)

    with pytest.raises(ValueError):
        service.delete_credential("   ")

    repository.delete.assert_not_called()

def test_delete_credential_rejects_empty_profile_name() -> None:
    repository = Mock(spec=CredentialsRepository)
    service = CredentialService(repository)

    with pytest.raises(ValueError):
        service.delete_credential(
            provider="gemini",
            name="   ",
        )

    repository.delete.assert_not_called()

def test_delete_credential_returns_repository_result() -> None:
    repository = Mock(spec=CredentialsRepository)
    repository.delete.return_value = True

    service = CredentialService(repository)

    result = service.delete_credential(" Gemini ", " Default ")

    assert result is True
    repository.delete.assert_called_once_with(
        "gemini",
        "default",
    )

def test_delete_credential_returns_false_when_not_found() -> None:
    repository = Mock(spec=CredentialsRepository)
    repository.delete.return_value = False

    service = CredentialService(repository)

    result = service.delete_credential("gemini", "default")

    assert result is False