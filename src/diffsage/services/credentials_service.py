import os

from diffsage.exceptions import CredentialNotFoundError, InvalidCredentialError
from diffsage.models.credentials import Credential
from diffsage.storage.credentials_repository import CredentialsRepository

API_KEY_ENVIRONMENT_VARIABLE = "DIFFSAGE_API_KEY"


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
            raise InvalidCredentialError("Provider cannot be empty.")

        if not name:
            raise InvalidCredentialError("Credential profile name cannot be empty.")

        if not api_key:
            raise InvalidCredentialError("API key cannot be empty.")

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
            raise InvalidCredentialError("Provider cannot be empty.")

        if not name:
            raise InvalidCredentialError("Credential profile name cannot be empty.")

        return self._repository.get(provider, name)

    @staticmethod
    def environment_api_key() -> str | None:
        """Return DIFFSAGE_API_KEY, or None when it is not set.

        Set but empty is an error rather than "not set": in CI it usually means a secret
        that did not reach the job, and falling back to a stored key would hide that.
        """

        value = os.environ.get(API_KEY_ENVIRONMENT_VARIABLE)

        if value is None:
            return None

        value = value.strip()

        if not value:
            raise InvalidCredentialError(
                f"{API_KEY_ENVIRONMENT_VARIABLE} is set but empty. Set it to your API key, "
                "or unset it to use the stored credentials."
            )

        return value

    def resolve_credential(self, provider: str, name: str = "default") -> Credential:
        """Return the credential AI commands should use.

        DIFFSAGE_API_KEY wins over the credentials file, matching how DIFFSAGE_*
        variables override config files.
        """

        api_key = self.environment_api_key()

        if api_key is not None:
            return Credential(
                provider=self._NORMALIZERS["provider"](provider.strip()),
                name=API_KEY_ENVIRONMENT_VARIABLE,
                api_key=api_key,
            )

        credential = self.get_credential(provider, name)

        if credential is None:
            raise CredentialNotFoundError(
                provider,
                name,
                hint=f"Run 'diffsage auth set {provider}', or set {API_KEY_ENVIRONMENT_VARIABLE}.",
            )

        return credential

    def list_credentials(self) -> list[Credential]:
        return self._repository.list()

    def delete_credential(self, provider: str, name: str = "default") -> bool:
        provider = self._NORMALIZERS["provider"](provider.strip())
        name = self._NORMALIZERS["name"](name.strip())

        if not provider:
            raise InvalidCredentialError("Provider cannot be empty.")

        if not name:
            raise InvalidCredentialError("Credential profile cannot be empty.")

        return self._repository.delete(provider, name)
