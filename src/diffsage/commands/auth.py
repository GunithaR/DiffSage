import typer

from diffsage.config.paths import get_credentials_path
from diffsage.logging.logger import get_logger
from diffsage.services.credentials_service import CredentialService
from diffsage.storage.credentials_repository import CredentialsRepository
from diffsage.ui.auth_view import AuthView

logger = get_logger(__name__)

app = typer.Typer(
    help="DiffSage credential management",
    invoke_without_command=False,
)


@app.command("set")
def set_credential(
    provider: str,
    api_key: str,
    name: str = typer.Option(
        "default",
        "--name",
        help="Credential profile name.",
    )
) -> None:
    """Store a DiffSage provider credential."""

    view = AuthView()

    try:
        path = get_credentials_path()
        repository = CredentialsRepository(path)
        service = CredentialService(repository)

        service.set_credential(
            provider,
            api_key,
            name,
        )

        view.show_success("Credential saved.")

    except ValueError as e:
        logger.warning(str(e))
        view.show_error(str(e))
        raise SystemExit(1) from None

    except Exception:
        logger.exception("Unexpected error while executing auth command.")
        view.show_error(
            "An unexpected error occurred. Please check the log file for more details."
        )
        raise SystemExit(1) from None

@app.command("get")
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

    try:
        path = get_credentials_path()
        repository = CredentialsRepository(path)
        service = CredentialService(repository)

        credential = service.get_credential(
            provider,
            name,
        )

        if credential is None:
            view.show_error(
                f"Credential not found for provider '{provider}' "
                f"and profile '{name}'."
            )
            raise SystemExit(1)

        view.show_credential(credential)

    except ValueError as e:
        logger.warning(str(e))
        view.show_error(str(e))
        raise SystemExit(1) from None

    except Exception:
        logger.exception("Unexpected error while executing auth command.")
        view.show_error(
            "An unexpected error occurred. Please check the log file for more details."
        )
        raise SystemExit(1) from None

@app.command("list")
def list_credentials() -> None:
    """List configured DiffSage credentials."""

    view = AuthView()

    try:
        path = get_credentials_path()
        repository = CredentialsRepository(path)
        service = CredentialService(repository)

        credentials = service.list_credentials()

        view.show_credentials(credentials)

    except Exception:
        logger.exception("Unexpected error while executing auth command.")
        view.show_error(
            "An unexpected error occurred. Please check the log file for more details."
        )
        raise SystemExit(1) from None

@app.command("unset")
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

    try:
        path = get_credentials_path()
        repository = CredentialsRepository(path)
        service = CredentialService(repository)

        deleted = service.delete_credential(
            provider,
            name,
        )

        if not deleted:
            view.show_error(
                f"Credential not found for provider '{provider}' "
                f"and profile '{name}'."
            )
            raise SystemExit(1)

        view.show_success("Credential removed.")

    except ValueError as e:
        logger.warning(str(e))
        view.show_error(str(e))
        raise SystemExit(1) from None

    except Exception:
        logger.exception("Unexpected error while executing auth command.")
        view.show_error(
            "An unexpected error occurred. Please check the log file for more details."
        )
        raise SystemExit(1) from None