import typer

from diffsage.commands.error_handler import handle_command_errors
from diffsage.config.loader import load_settings, load_settings_or_defaults
from diffsage.config.resolver import configuration_sources, resolve_config_path
from diffsage.config.scope import ConfigScope
from diffsage.exceptions import ConfigError
from diffsage.logging.logger import get_logger
from diffsage.services.config_service import ConfigService
from diffsage.storage.config_repository import ConfigRepository
from diffsage.ui.config_view import ConfigView

logger = get_logger(__name__)

app = typer.Typer(help="DiffSage configuration", invoke_without_command=False)

READ_LOCAL_HELP = "Read the repository's .diffsage.toml directly, instead of the resolved values."
READ_GLOBAL_HELP = "Read your user-wide config file directly, instead of the resolved values."


def _resolve_scope(*, local: bool, global_: bool) -> ConfigScope:
    if local and global_:
        raise ConfigError("Cannot specify both --local and --global.")

    if local:
        return ConfigScope.LOCAL

    return ConfigScope.GLOBAL


@app.command("list")
@handle_command_errors("config list")
def list_config(
    local: bool = typer.Option(False, "--local", help=READ_LOCAL_HELP),
    global_: bool = typer.Option(False, "--global", help=READ_GLOBAL_HELP),
) -> None:
    """List the current DiffSage configuration."""

    view = ConfigView()

    # Reading a file directly must work even when the configuration is broken.
    settings = load_settings_or_defaults() if local or global_ else load_settings()
    scope = _resolve_scope(
        local=local,
        global_=global_,
    )

    if local or global_:
        path = resolve_config_path(scope)

        repository = ConfigRepository(path)
        service = ConfigService(settings, repository)

        view.show_path(path)
        view.show_configuration(service.get_configuration_raw())
        return

    service = ConfigService(settings)

    view.show_sources(configuration_sources())
    view.show_configuration(service.get_configuration())


@app.command("get")
@handle_command_errors("config get")
def get_config(
    key: str,
    local: bool = typer.Option(False, "--local", help=READ_LOCAL_HELP),
    global_: bool = typer.Option(False, "--global", help=READ_GLOBAL_HELP),
) -> None:
    """Get the value of a DiffSage configuration."""

    view = ConfigView()

    # Reading a file directly must work even when the configuration is broken.
    settings = load_settings_or_defaults() if local or global_ else load_settings()

    if local or global_:
        scope = _resolve_scope(
            local=local,
            global_=global_,
        )

        path = resolve_config_path(scope)
        repository = ConfigRepository(path)
        service = ConfigService(settings, repository)

        report = service.get_configuration_value_raw(key.strip().lower())

        view.show_path(path)
        view.show_value(report)
        return

    service = ConfigService(settings)
    report = service.get_value(key.strip().lower())

    view.show_sources(configuration_sources())
    view.show_value(report)


@app.command("set")
@handle_command_errors("config set")
def set_config(
    key: str,
    value: str,
    local: bool = typer.Option(False, "--local", help="Write to the repository's .diffsage.toml."),
    global_: bool = typer.Option(
        False, "--global", help="Write to your user-wide config file (the default)."
    ),
) -> None:
    """Set the value of a DiffSage configuration."""

    view = ConfigView()

    # Writing must work even when the configuration is broken, so it can be repaired.
    settings = load_settings_or_defaults()

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
        False, "--local", help="Remove from the repository's .diffsage.toml."
    ),
    global_: bool = typer.Option(
        False, "--global", help="Remove from your user-wide config file (the default)."
    ),
) -> None:
    """Remove a DiffSage configuration value."""

    view = ConfigView()

    # Writing must work even when the configuration is broken, so it can be repaired.
    settings = load_settings_or_defaults()

    scope = _resolve_scope(local=local, global_=global_)
    path = resolve_config_path(scope)
    repository = ConfigRepository(path)

    service = ConfigService(settings, repository)

    report = service.unset_value(key.strip().lower())

    view.show_success(f"{scope.value.capitalize()} configuration removed.")
    view.show_path(path)
    view.show_configuration(report)
