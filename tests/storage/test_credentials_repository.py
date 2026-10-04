import os
import stat
from pathlib import Path

import pytest

from diffsage.config.paths import display_path
from diffsage.exceptions import InvalidCredentialsFileError
from diffsage.models.credentials import Credential
from diffsage.storage.credentials_repository import CredentialsRepository


def test_save_and_get_credential(tmp_path: Path) -> None:
    path = tmp_path / "credentials.toml"

    credential = Credential(provider="gemini", name="default", api_key="test-api-key")

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


def test_save_supports_multiple_profiles_for_same_provider(tmp_path: Path) -> None:
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


def test_list_returns_empty_when_credentials_file_does_not_exist(tmp_path: Path) -> None:
    path = tmp_path / "credentials.toml"

    repository = CredentialsRepository(path)

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


@pytest.mark.skipif(os.name != "posix", reason="Unix permission bits only")
def test_save_creates_owner_only_file(tmp_path: Path) -> None:
    path = tmp_path / "credentials.toml"

    CredentialsRepository(path).save(Credential("gemini", "default", "secret-key"))

    assert stat.S_IMODE(path.stat().st_mode) == 0o600


@pytest.mark.skipif(os.name != "posix", reason="Unix permission bits only")
def test_reading_an_old_world_readable_file_tightens_it(tmp_path: Path) -> None:
    """Regression: older versions created credentials.toml as -rw-r--r--."""

    path = tmp_path / "credentials.toml"
    path.write_text('[credentials.gemini.default]\napi_key = "secret-key"\n')
    os.chmod(path, 0o644)

    credential = CredentialsRepository(path).get("gemini")

    assert credential is not None
    assert stat.S_IMODE(path.stat().st_mode) == 0o600


def test_unparseable_credentials_file_raises_clear_error(tmp_path: Path) -> None:
    path = tmp_path / "credentials.toml"
    path.write_text("[credentials.gemini.default\napi_key = x\n")

    with pytest.raises(InvalidCredentialsFileError) as error:
        CredentialsRepository(path).list()

    assert "Invalid TOML syntax in" in str(error.value)
    assert "run 'diffsage auth set' again" in str(error.value)


@pytest.mark.parametrize(
    ("content", "problem"),
    [
        ('credentials = "oops"\n', "'credentials' should be a table, not string"),
        (
            '[credentials]\ngemini = "my-key"\n',
            "'credentials.gemini' should be a table, not string",
        ),
        (
            "[credentials.gemini]\ndefault = 5\n",
            "'credentials.gemini.default' should be a table, not integer",
        ),
        (
            "[credentials.gemini.default]\napi_key = 123\n",
            "'credentials.gemini.default.api_key' should be a non-empty string",
        ),
        (
            '[credentials.gemini.default]\napi_key = "  "\n',
            "'credentials.gemini.default.api_key' should be a non-empty string",
        ),
    ],
)
@pytest.mark.parametrize("operation", ["list", "get"])
def test_malformed_credentials_file_is_reported(
    tmp_path: Path, content, problem, operation
) -> None:
    """Regression: a value of the wrong type crashed with "'str' object has no attribute
    'get'", which users saw as an unexpected error."""

    path = tmp_path / "credentials.toml"
    path.write_text(content)
    repository = CredentialsRepository(path)

    with pytest.raises(InvalidCredentialsFileError) as error:
        repository.list() if operation == "list" else repository.get("gemini")

    assert f"Invalid credentials file {display_path(path)}: {problem}." in str(error.value)
    assert path.read_text() == content


def test_save_reports_malformed_file_instead_of_overwriting_it(tmp_path: Path) -> None:
    path = tmp_path / "credentials.toml"
    path.write_text('[credentials]\ngemini = "my-key"\n')

    with pytest.raises(InvalidCredentialsFileError, match="'credentials.gemini' should be a table"):
        CredentialsRepository(path).save(Credential("gemini", "default", "new-key"))

    assert path.read_text() == '[credentials]\ngemini = "my-key"\n'


def test_inline_tables_are_valid_credentials(tmp_path: Path) -> None:
    path = tmp_path / "credentials.toml"
    path.write_text('credentials = { gemini = { default = { api_key = "inline-key" } } }\n')
    repository = CredentialsRepository(path)

    assert repository.get("gemini") == Credential("gemini", "default", "inline-key")
    assert repository.list() == [Credential("gemini", "default", "inline-key")]

    repository.save(Credential("gemini", "paid", "paid-key"))

    assert repository.get("gemini", "paid") == Credential("gemini", "paid", "paid-key")
    assert repository.get("gemini") == Credential("gemini", "default", "inline-key")
