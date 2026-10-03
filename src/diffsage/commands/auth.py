import typer

from diffsage.commands.error_handler import handle_command_errors
from diffsage.config.paths import get_credentials_path
from diffsage.exceptions import CredentialNotFoundError
from diffsage.logging.logger import get_logger
from diffsage.services.credentials_service import CredentialService
from diffsage.storage.credentials_repository import CredentialsRepository
from diffsage.ui.auth_view import AuthView

logger = get_logger(__name__)

app = typer.Typer(
    help="DiffSage credential management",
    invoke_without_command=False,
)


def _credential_service() -> CredentialService:
    path = get_credentials_path()
    repository = CredentialsRepository(path)
    return CredentialService(repository)


@app.command("set")
@handle_command_errors("auth set")
def set_credential(
    provider: str,
    api_key: str,
    name: str = typer.Option(
        "default",
        "--name",
        help="Credential profile name.",
    ),
) -> None:
    """Store a DiffSage provider credential."""

    view = AuthView()

    _credential_service().set_credential(
        provider,
        api_key,
        name,
    )

    view.show_success("Credential saved.")


@app.command("get")
@handle_command_errors("auth get")
def get_credential(
    provider: str,
    name: str = typer.Option(
        "default",
        "--name",
        help="Credential profile name.",
    ),
) -> None:
    """Get a DiffSage provider credential."""

    view = AuthView()

    credential = _credential_service().get_credential(
        provider,
        name,
    )

    if credential is None:
        raise CredentialNotFoundError(provider, name)

    view.show_credential(credential)


@app.command("list")
@handle_command_errors("auth list")
def list_credentials() -> None:
    """List configured DiffSage credentials."""

    view = AuthView()

    credentials = _credential_service().list_credentials()

    view.show_credentials(credentials)


@app.command("unset")
@handle_command_errors("auth unset")
def unset_credential(
    provider: str,
    name: str = typer.Option(
        "default",
        "--name",
        help="Credential profile name.",
    ),
) -> None:
    """Unset DiffSage provider credential."""

    view = AuthView()

    deleted = _credential_service().delete_credential(
        provider,
        name,
    )

    if not deleted:
        raise CredentialNotFoundError(provider, name)

    view.show_success("Credential removed.")
