from pathlib import Path

from tomlkit import document, parse, table

from diffsage.models.credentials import Credential


class CredentialsRepository:
    """Persists DiffSage API keys configuration."""

    def __init__(self, path: Path) -> None:
        self._path = path

    def save(self, credential: Credential) -> None:
        if self._path.exists():
            doc = parse(self._path.read_text())
        else:
            doc = document()

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

        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(doc.as_string())

    def get(self, provider: str, name: str = "default") -> Credential | None: 
        if not self._path.exists():
            return None

        doc = parse(self._path.read_text())
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
        if  not self._path.exists():
            return []

        doc = parse(self._path.read_text())
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
                    Credential(
                        provider=provider_name,
                        name=profile_name,
                        api_key=api_key
                    )
                )

        return result

    def delete(self, provider: str, name: str = "default") -> bool:
        if not self._path.exists():
            return False

        doc = parse(self._path.read_text())
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

        self._path.write_text(doc.as_string())

        return True
