from diffsage.models.credentials import Credential
from diffsage.storage.credentials_repository import CredentialsRepository


class CredentialService:
    _NORMALIZERS = {
        "provider": str.lower,
        "name": str.lower,
    }

    def __init__(self, repository: CredentialsRepository) -> None:
        self._repository = repository

    def set_credential(self, provider: str, api_key: str, name: str = "default") -> None:
        provider = self._NORMALIZERS["provider"](provider.strip())
        name = self._NORMALIZERS["name"](name.strip())
        api_key = api_key.strip()

        if not provider:
            raise ValueError("Provider cannot be empty.")

        if not name:
            raise ValueError("Credential profile name cannot be empty.")

        if not api_key:
            raise ValueError("API key cannot be empty.")

        credential = Credential(
            provider=provider,
            name=name,
            api_key=api_key,
        )

        self._repository.save(credential)

    def get_credential(self, provider: str, name: str = "default") -> Credential | None:
        provider = self._NORMALIZERS["provider"](provider.strip())
        name = self._NORMALIZERS["name"](name.strip())

        if not provider:
            raise ValueError("Provider cannot be empty.")

        if not name:
            raise ValueError("Credential profile name cannot be empty.")

        return self._repository.get(provider, name)

    def list_credentials(self) -> list[Credential]:
        return self._repository.list()

    def delete_credential(self, provider: str, name: str = "default") -> bool:
        provider = self._NORMALIZERS["provider"](provider.strip())
        name = self._NORMALIZERS["name"](name.strip())

        if not provider:
            raise ValueError("Provider cannot be empty.")

        if not name:
            raise ValueError("Credential profile cannot be empty.")

        return self._repository.delete(provider, name)
