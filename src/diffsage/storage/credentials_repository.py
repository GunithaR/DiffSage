from pathlib import Path

from tomlkit import TOMLDocument, document, parse, table
from tomlkit.exceptions import ParseError

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

    def save(self, credential: Credential) -> None:
        doc = self._read() or document()

        credentials = doc.get("credentials")

        if "credentials" not in doc:
            credentials = table()
            doc["credentials"] = credentials

        provider = credentials.get(credential.provider)

        if provider is None:
            provider = table()
            credentials[credential.provider] = provider

        profile = provider.get(credential.name)

        if profile is None:
            profile = table()
            provider[credential.name] = profile

        profile["api_key"] = credential.api_key

        self._write(doc)

    def get(self, provider: str, name: str = "default") -> Credential | None:
        doc = self._read()

        if doc is None:
            return None

        credentials = doc.get("credentials")

        if credentials is None:
            return None

        provider_table = credentials.get(provider)
        if provider_table is None:
            return None

        profile = provider_table.get(name)
        if profile is None:
            return None

        api_key = profile.get("api_key")
        if api_key is None:
            return None

        return Credential(
            provider=provider,
            name=name,
            api_key=api_key,
        )

    def list(self) -> list[Credential]:
        doc = self._read()

        if doc is None:
            return []

        credentials = doc.get("credentials")

        if credentials is None:
            return []

        result: list[Credential] = []

        for provider_name, provider in credentials.items():
            for profile_name, profile in provider.items():
                api_key = profile.get("api_key")

                if api_key is None:
                    continue

                result.append(
                    Credential(provider=provider_name, name=profile_name, api_key=api_key)
                )

        return result

    def delete(self, provider: str, name: str = "default") -> bool:
        doc = self._read()

        if doc is None:
            return False

        credentials = doc.get("credentials")

        if credentials is None:
            return False

        provider_table = credentials.get(provider)

        if provider_table is None:
            return False

        if provider_table.get(name) is None:
            return False

        del provider_table[name]

        if not provider_table:
            del credentials[provider]

        self._write(doc)

        return True
