import re
from typing import Any

import typer
from typer.core import TyperCommand

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


_NEGATIVE_NUMBER = re.compile(r"^-\d+(\.\d+)?$")


class _AcceptsNegativeNumbers(TyperCommand):
    """Read a negative number such as -5 as a value, not as an unknown option.

    Click treats every argument starting with "-" as an option, so `config set timeout -5`
    failed with "No such option: -5" before the value could be validated. Negative
    numbers are moved behind "--" (end of options), where Click reads them as arguments;
    options and the key keep their order in front, so misspelled options are still
    reported as unknown options.
    """

    # ctx is only passed on; its type is Click's Context, which Typer vendors privately.
    def parse_args(self, ctx: Any, args: list[str]) -> list[str]:
        if "--" not in args:
            numbers = [arg for arg in args if _NEGATIVE_NUMBER.match(arg)]

            if numbers:
                rest = [arg for arg in args if not _NEGATIVE_NUMBER.match(arg)]
                args = [*rest, "--", *numbers]

        return super().parse_args(ctx, args)


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


@app.command("set", cls=_AcceptsNegativeNumbers)
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
