from diffsage.exceptions.base import DiffSageError


class CredentialNotFoundError(DiffSageError):
    """Raised when a required provider credential cannot be found."""

    def __init__(self, provider: str, name: str = "default") -> None:
        super().__init__(f"Credential not found for provider '{provider}' and profile '{name}'.")
