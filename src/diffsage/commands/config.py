import typer

from diffsage.commands.error_handler import handle_command_errors
from diffsage.config.loader import load_settings
from diffsage.config.resolver import get_local_config_path, resolve_config_path
from diffsage.config.scope import ConfigScope
from diffsage.exceptions import ConfigError
from diffsage.logging.logger import get_logger
from diffsage.services.config_service import ConfigService
from diffsage.storage.config_repository import ConfigRepository
from diffsage.ui.config_view import ConfigView

logger = get_logger(__name__)

app = typer.Typer(help="DiffSage configuration", invoke_without_command=False)


def _resolve_scope(*, local: bool, global_: bool) -> ConfigScope:
    if local and global_:
        raise ConfigError("Cannot specify both --local and --global.")

    if local:
        return ConfigScope.LOCAL

    return ConfigScope.GLOBAL


@app.command("list")
@handle_command_errors("config list")
def list_config(
    local: bool = typer.Option(False, "--local"), global_: bool = typer.Option(False, "--global")
) -> None:
    """List the current DiffSage configuration."""

    view = ConfigView()

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


@app.command("get")
@handle_command_errors("config get")
def get_config(
    key: str,
    local: bool = typer.Option(False, "--local"),
    global_: bool = typer.Option(False, "--global"),
) -> None:
    """Get the value of a DiffSage configuration."""

    view = ConfigView()

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


@app.command("set")
@handle_command_errors("config set")
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

    settings = load_settings()

    scope = _resolve_scope(local=local, global_=global_)
    path = resolve_config_path(scope)
    repository = ConfigRepository(path)

    service = ConfigService(settings, repository)

    report = service.set_value(key.strip().lower(), value)

    view.show_success(f"{scope.value.capitalize()} configuration updated.")
    view.show_path(path)
    view.show_configuration(report)


@app.command("unset")
@handle_command_errors("config unset")
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

    settings = load_settings()

    scope = _resolve_scope(local=local, global_=global_)
    path = resolve_config_path(scope)
    repository = ConfigRepository(path)

    service = ConfigService(settings, repository)

    report = service.unset_value(key.strip().lower())

    view.show_success(f"{scope.value.capitalize()} configuration removed.")
    view.show_path(path)
    view.show_configuration(report)
