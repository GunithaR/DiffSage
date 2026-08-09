from pathlib import Path

from diffsage.models.credentials import Credential
from diffsage.storage.credentials_repository import CredentialsRepository


def test_save_and_get_credential(tmp_path: Path) -> None:
    path = tmp_path / "credentials.toml"

    credential = Credential(
        provider="gemini",
        name="default",
        api_key="test-api-key"
    )

    repository = CredentialsRepository(path)
    repository.save(credential)

    result = repository.get("gemini", "default")

    assert result == credential

def test_get_returns_none_for_missing_credential(tmp_path: Path) -> None:
    path = tmp_path / "credentials.toml"

    credential = Credential(
        provider="gemini",
        name="default",
        api_key="test-api-key",
    )

    repository = CredentialsRepository(path)
    repository.save(credential)

    result = repository.get("openai", "default")

    assert result is None

def test_get_returns_none_when_credentials_file_does_not_exist(
    tmp_path: Path,
) -> None:
    path = tmp_path / "credentials.toml"

    repository = CredentialsRepository(path)

    result = repository.get("gemini", "default")

    assert result is None

def test_save_supports_multiple_profiles_for_same_provider(
    tmp_path: Path
) -> None:
    path = tmp_path / "crendetials.toml"

    default = Credential(
        provider="gemini",
        name="default",
        api_key="default-key",
    )

    paid = Credential(
        provider="gemini",
        name="paid",
        api_key="paid-key",
    )

    repository = CredentialsRepository(path)
    repository.save(default)
    repository.save(paid)

    assert repository.get("gemini", "default") == default
    assert repository.get("gemini", "paid") == paid

def test_list_returns_all_credentials(tmp_path: Path) -> None:
    path = tmp_path / "credentials.toml"

    gemini = Credential(
        provider="gemini",
        name="default",
        api_key="gemini-key",
    )

    openai = Credential(
        provider="openai",
        name="default",
        api_key="openai-key",
    )

    repository = CredentialsRepository(path)
    repository.save(gemini)
    repository.save(openai)

    result = repository.list()

    assert result == [gemini, openai]

def test_list_returns_empty_when_credentials_file_does_not_exist(
    tmp_path: Path
) -> None:
    path = tmp_path / "credentials.toml"

    repository =  CredentialsRepository(path)

    result = repository.list()

    assert result == []

def test_list_returns_empty_for_empty_credentials_file(tmp_path: Path) -> None:
    path = tmp_path / "credentials.toml"
    path.touch()

    repository = CredentialsRepository(path)

    result = repository.list()

    assert result == []

def test_delete_removes_empty_provider_table(tmp_path: Path) -> None:
    path = tmp_path / "credentials.toml"

    credential = Credential(
        provider="gemini",
        name="default",
        api_key="gemini-key",
    )

    repository = CredentialsRepository(path)
    repository.save(credential)

    repository.delete("gemini", "default")

    assert repository.list() == []

def test_delete_removes_only_requested_profile(tmp_path: Path) -> None:
    path = tmp_path / "credentials.toml"

    default = Credential(
        provider="gemini",
        name="default",
        api_key="default-key",
    )

    paid = Credential(
        provider="gemini",
        name="paid",
        api_key="paid-key",
    )

    repository = CredentialsRepository(path)
    repository.save(default)
    repository.save(paid)

    repository.delete("gemini", "default")

    assert repository.get("gemini", "default") is None
    assert repository.get("gemini", "paid") == paid

def test_delete_returns_true_when_credential_exists(tmp_path: Path) -> None:
    path = tmp_path / "credentials.toml"

    credential = Credential(
        provider="gemini",
        name="default",
        api_key="test-api-key",
    )

    repository = CredentialsRepository(path)
    repository.save(credential)

    result = repository.delete("gemini", "default")

    assert result is True
    assert repository.get("gemini", "default") is None

def test_delete_returns_false_when_credential_does_not_exist(tmp_path: Path) -> None:
    path = tmp_path / "credentials.toml"

    repository = CredentialsRepository(path)

    result = repository.delete("gemini", "default")

    assert result is False
