import logging
from importlib.metadata import version

import typer

from diffsage.commands.ask import ask
from diffsage.commands.auth import app as auth_app
from diffsage.commands.commit import commit
from diffsage.commands.config import app as config_app
from diffsage.commands.doctor import doctor
from diffsage.commands.error_handler import handle_command_errors
from diffsage.commands.pr import pr
from diffsage.config.loader import load_settings
from diffsage.exceptions import ConfigError
from diffsage.logging.logger import configure_logging

app = typer.Typer(help="DiffSage: AI-aware Git workflow toolkit")

# Commands that must run even when the configuration is invalid, so it can be
# repaired (`config`) or diagnosed (`doctor`).
CONFIG_TOLERANT_COMMANDS = {"config", "doctor"}


def version_callback(value: bool) -> None:
    if value:
        typer.echo(version("diffsage"))
        raise typer.Exit()


@app.callback()
@handle_command_errors("diffsage")
def main(
    ctx: typer.Context,
    _version: bool = typer.Option(
        False,
        "--version",
        "-v",
        callback=version_callback,
        is_eager=True,
        help="Show the Diffsage version.",
    ),
) -> None:
    """
    Initialize DiffSage.
    """
    try:
        settings = load_settings()
    except ConfigError:
        # Start the log file at the default level so the error handler's warning is
        # written there, instead of to stderr through Python's last-resort handler.
        configure_logging()

        if ctx.invoked_subcommand in CONFIG_TOLERANT_COMMANDS:
            return

        raise

    configure_logging(
        getattr(
            logging,
            settings.log_level.upper(),
            logging.INFO,
        )
    )


app.command()(doctor)
app.command()(ask)
app.command()(commit)
app.command()(pr)

app.add_typer(
    config_app,
    name="config",
)
app.add_typer(
    auth_app,
    name="auth",
)
