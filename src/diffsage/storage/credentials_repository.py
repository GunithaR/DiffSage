from collections.abc import MutableMapping
from pathlib import Path
from typing import Any

from tomlkit import TOMLDocument, document, inline_table, parse, table
from tomlkit.exceptions import ParseError
from tomlkit.items import InlineTable

from diffsage.config.paths import display_path
from diffsage.exceptions import InvalidCredentialsFileError
from diffsage.models.credentials import Credential
from diffsage.storage.files import restrict_to_owner, write_private_text


class CredentialsRepository:
    """Persists DiffSage API keys configuration."""

    def __init__(self, path: Path) -> None:
        self._path = path

    def _read(self) -> TOMLDocument | None:
        """Parse the credentials file, or return None if it does not exist yet."""

        if not self._path.exists():
            return None

        # Older versions created this file readable by every local user.
        restrict_to_owner(self._path)

        try:
            return parse(self._path.read_text(encoding="utf-8"))
        except ParseError as error:
            raise InvalidCredentialsFileError(
                f"Invalid TOML syntax in {display_path(self._path)}: {error}. "
                "Fix that line in a text editor, or delete the file and run "
                "'diffsage auth set' again."
            ) from error

    def _write(self, doc: TOMLDocument) -> None:
        write_private_text(self._path, doc.as_string())

    def _invalid(self, problem: str) -> InvalidCredentialsFileError:
        return InvalidCredentialsFileError(
            f"Invalid credentials file {display_path(self._path)}: {problem}. Fix it in a text "
            "editor, or delete the file and run 'diffsage auth set' again."
        )

    def _check_table(self, value: object, location: str) -> MutableMapping[str, Any]:
        """A hand-edited file can hold any TOML value; report anything that is not a table
        instead of crashing later with an attribute error."""

        if not isinstance(value, MutableMapping):
            raise self._invalid(
                f"'{location}' should be a table, not {type(value).__name__.lower()}"
            )

        return value

    def _table(
        self, parent: MutableMapping[str, Any], key: str, location: str
    ) -> MutableMapping[str, Any] | None:
        """Return the table at parent[key], or None when it is missing."""

        value = parent.get(key)
        return None if value is None else self._check_table(value, location)

    def _ensure_table(
        self, parent: MutableMapping[str, Any], key: str, location: str
    ) -> MutableMapping[str, Any]:
        """Return the table at parent[key], creating it when it is missing."""

        if parent.get(key) is None:
            # TOML does not allow a [table] inside an inline { } table.
            parent[key] = inline_table() if isinstance(parent, InlineTable) else table()

        return self._check_table(parent[key], location)

    def _api_key(self, profile: MutableMapping[str, Any], location: str) -> str | None:
        api_key = profile.get("api_key")

        if api_key is None:
            return None

        if not isinstance(api_key, str) or not api_key.strip():
            raise self._invalid(f"'{location}.api_key' should be a non-empty string")

        return api_key

    def save(self, credential: Credential) -> None:
        doc = self._read() or document()
        location = f"credentials.{credential.provider}.{credential.name}"

        credentials = self._ensure_table(doc, "credentials", "credentials")
        provider = self._ensure_table(
            credentials, credential.provider, f"credentials.{credential.provider}"
        )
        profile = self._ensure_table(provider, credential.name, location)

        profile["api_key"] = credential.api_key

        self._write(doc)

    def get(self, provider: str, name: str = "default") -> Credential | None:
        doc = self._read()

        if doc is None:
            return None

        credentials = self._table(doc, "credentials", "credentials")
        provider_table = credentials and self._table(
            credentials, provider, f"credentials.{provider}"
        )
        profile = provider_table and self._table(
            provider_table, name, f"credentials.{provider}.{name}"
        )

        if not profile:
            return None

        api_key = self._api_key(profile, f"credentials.{provider}.{name}")

        if api_key is None:
            return None

        return Credential(provider=provider, name=name, api_key=api_key)

    def list(self) -> list[Credential]:
        doc = self._read()

        if doc is None:
            return []

        credentials = self._table(doc, "credentials", "credentials")

        if credentials is None:
            return []

        result: list[Credential] = []

        for provider_name in list(credentials):
            provider = self._check_table(credentials[provider_name], f"credentials.{provider_name}")

            for profile_name in list(provider):
                location = f"credentials.{provider_name}.{profile_name}"
                profile = self._check_table(provider[profile_name], location)
                api_key = self._api_key(profile, location)

                if api_key is not None:
                    result.append(
                        Credential(provider=provider_name, name=profile_name, api_key=api_key)
                    )

        return result

    def delete(self, provider: str, name: str = "default") -> bool:
        doc = self._read()

        if doc is None:
            return False

        credentials = self._table(doc, "credentials", "credentials")
        provider_table = credentials and self._table(
            credentials, provider, f"credentials.{provider}"
        )

        if not credentials or not provider_table or provider_table.get(name) is None:
            return False

        del provider_table[name]

        if not provider_table:
            del credentials[provider]

        self._write(doc)

        return True
