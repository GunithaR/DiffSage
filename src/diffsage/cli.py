import logging

import typer

from diffsage.commands.ask import ask
from diffsage.commands.auth import app as auth_app
from diffsage.commands.commit import commit
from diffsage.commands.config import app as config_app
from diffsage.commands.doctor import doctor
from diffsage.commands.pr import pr
from diffsage.config.loader import load_settings
from diffsage.logging.logger import configure_logging

app = typer.Typer(help="DiffSage: AI-aware Git workflow toolkit")


@app.callback()
def main() -> None:
    """
    Initialize DiffSage.
    """
    settings = load_settings()
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
