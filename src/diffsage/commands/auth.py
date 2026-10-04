import sys

import typer

from diffsage.commands.error_handler import handle_command_errors
from diffsage.config.paths import get_credentials_path
from diffsage.exceptions import CredentialNotFoundError, InvalidCredentialError
from diffsage.logging.logger import get_logger
from diffsage.services.credentials_service import API_KEY_ENVIRONMENT_VARIABLE, CredentialService
from diffsage.storage.credentials_repository import CredentialsRepository
from diffsage.ui.auth_view import AuthView

logger = get_logger(__name__)

app = typer.Typer(
    help="DiffSage credential management",
    invoke_without_command=False,
)


def _stdin_is_terminal() -> bool:
    return sys.stdin.isatty()


def _read_api_key(provider: str) -> str:
    """Ask for the key at a hidden prompt, or read it from piped input."""

    if _stdin_is_terminal():
        return typer.prompt(f"API key for {provider}", hide_input=True)

    # Piped input (scripts, CI): nothing to hide on screen, so no prompt. Using the
    # hidden prompt here would print getpass's "input may be echoed" warning.
    api_key = sys.stdin.readline().strip()

    if not api_key:
        raise InvalidCredentialError("No API key was received on standard input.")

    return api_key


def _warn_if_environment_key_is_set(view: AuthView) -> None:
    if CredentialService.environment_api_key() is not None:
        view.show_warning(
            f"{API_KEY_ENVIRONMENT_VARIABLE} is set, so AI commands use it instead of "
            "stored credentials."
        )


def _credential_service() -> CredentialService:
    path = get_credentials_path()
    repository = CredentialsRepository(path)
    return CredentialService(repository)


@app.command("set")
@handle_command_errors("auth set")
def set_credential(
    provider: str,
    name: str = typer.Option(
        "default",
        "--name",
        help="Credential profile name.",
    ),
) -> None:
    """Store a DiffSage provider credential.

    The API key is entered at a hidden prompt, never as an argument.

    For scripts, pipe it in: printf '%s\\n' "$KEY" | diffsage auth set gemini
    """

    view = AuthView()

    api_key = _read_api_key(provider)

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

    _warn_if_environment_key_is_set(view)

    if credential is None:
        raise CredentialNotFoundError(provider, name)

    view.show_credential(credential)


@app.command("list")
@handle_command_errors("auth list")
def list_credentials() -> None:
    """List configured DiffSage credentials."""

    view = AuthView()

    credentials = _credential_service().list_credentials()

    _warn_if_environment_key_is_set(view)
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
