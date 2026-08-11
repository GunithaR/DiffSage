import typer

from diffsage.config.loader import load_settings
from diffsage.config.resolver import get_local_config_path, resolve_config_path
from diffsage.config.scope import ConfigScope
from diffsage.exceptions import InvalidConfigurationValueError, UnknownConfigurationKeyError
from diffsage.logging.logger import get_logger
from diffsage.services.config_service import ConfigService
from diffsage.storage.config_repository import ConfigRepository
from diffsage.ui.config_view import ConfigView

logger = get_logger(__name__)

app = typer.Typer(help="DiffSage configuration", invoke_without_command=False)


def _resolve_scope(*, local: bool, global_: bool) -> ConfigScope:
    if local and global_:
        raise typer.BadParameter("Cannot specify both --local and --global.")

    if local:
        return ConfigScope.LOCAL

    return ConfigScope.GLOBAL


@app.command("list")
def list_config(
    local: bool = typer.Option(False, "--local"), global_: bool = typer.Option(False, "--global")
) -> None:
    """List the current DiffSage configuration."""

    view = ConfigView()

    try:
        settings = load_settings()
        scope = _resolve_scope(
            local=local,
            global_=global_,
        )

        if local or global_:
            path = resolve_config_path(scope)

            repository = ConfigRepository(path)
            service = ConfigService(settings, repository)

            report = service.get_configuration_raw()

        else:
            path = get_local_config_path()

            repository = ConfigRepository(path)
            service = ConfigService(settings, repository)

            report = service.get_configuration()

        view.show_path(path)
        view.show_configuration(report)

    except typer.BadParameter as e:
        logger.warning(str(e))
        view.show_error(str(e))
        raise SystemExit(1) from None

    except Exception:
        logger.exception("Unexpected error while executing config command.")
        view.show_error("An unexpected error occurred. Please check the log file for more details.")
        raise SystemExit(1) from None


@app.command("get")
def get_config(
    key: str,
    local: bool = typer.Option(False, "--local"),
    global_: bool = typer.Option(False, "--global"),
) -> None:
    """Get the value of a DiffSage configuration."""

    view = ConfigView()

    try:
        settings = load_settings()

        if local or global_:
            scope = _resolve_scope(
                local=local,
                global_=global_,
            )

            path = resolve_config_path(scope)
            repository = ConfigRepository(path)
            service = ConfigService(settings, repository)

            report = service.get_configuration_value_raw(key.strip().lower())

        else:
            path = get_local_config_path()
            repository = ConfigRepository(path)
            service = ConfigService(settings, repository)

            report = service.get_value(key.strip().lower())

        view.show_path(path)
        view.show_value(report)

    except UnknownConfigurationKeyError as e:
        logger.warning(str(e))
        view.show_error(str(e))
        raise SystemExit(1) from None

    except typer.BadParameter as e:
        logger.warning(str(e))
        view.show_error(str(e))
        raise SystemExit(1) from None

    except Exception:
        logger.exception("Unexpected error while executing config command.")
        view.show_error("An unexpected error occurred. Please check the log file for more details.")
        raise SystemExit(1) from None


@app.command("set")
def set_config(
    key: str,
    value: str,
    local: bool = typer.Option(
        False, "--local", help="Write to the repository's local configuration."
    ),
    global_: bool = typer.Option(
        False, "--global", help="Write to the repository's global configuration."
    ),
) -> None:
    """Set the value of a DiffSage configuration."""

    view = ConfigView()

    try:
        settings = load_settings()

        scope = _resolve_scope(local=local, global_=global_)
        path = resolve_config_path(scope)
        repository = ConfigRepository(path)

        service = ConfigService(settings, repository)

        report = service.set_value(key.strip().lower(), value)

        view.show_success(f"{scope.value.capitalize()} configuration updated.")
        view.show_path(path)
        view.show_configuration(report)

    except UnknownConfigurationKeyError as e:
        logger.warning(str(e))
        view.show_error(str(e))
        raise SystemExit(1) from None

    except InvalidConfigurationValueError as e:
        logger.warning(str(e))
        view.show_error(str(e))
        raise SystemExit(1) from None

    except typer.BadParameter as e:
        logger.warning(str(e))
        view.show_error(str(e))
        raise SystemExit(1) from None

    except Exception:
        logger.exception("Unexpected error while executing config command.")
        view.show_error("An unexpected error occurred. Please check the log file for more details.")
        raise SystemExit(1) from None


@app.command("unset")
def unset_config(
    key: str,
    local: bool = typer.Option(
        False, "--local", help="Write to the repository's local configuration."
    ),
    global_: bool = typer.Option(
        False, "--global", help="Write to the repository's global configuration."
    ),
) -> None:
    """Remove a DiffSage configuration value."""

    view = ConfigView()

    try:
        settings = load_settings()

        scope = _resolve_scope(local=local, global_=global_)
        path = resolve_config_path(scope)
        repository = ConfigRepository(path)

        service = ConfigService(settings, repository)

        report = service.unset_value(key.strip().lower())

        view.show_success(f"{scope.value.capitalize()} configuration removed.")
        view.show_path(path)
        view.show_configuration(report)

    except UnknownConfigurationKeyError as e:
        logger.warning(str(e))
        view.show_error(str(e))
        raise SystemExit(1) from None

    except typer.BadParameter as e:
        logger.warning(str(e))
        view.show_error(str(e))
        raise SystemExit(1) from None

    except Exception:
        logger.exception("Unexpected error while executing config command.")
        view.show_error("An unexpected error occurred. Please check the log file for more details.")
        raise SystemExit(1) from None
