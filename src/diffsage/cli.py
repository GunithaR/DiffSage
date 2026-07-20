import logging

import typer

from diffsage.commands.doctor import doctor
from diffsage.config.loader import load_settings
from diffsage.logging.logger import configure_logging

app = typer.Typer(help="DiffSage: AI-powered Git workflow assistant.")

settings = load_settings()
configure_logging(getattr(logging, settings.log_level.upper(), logging.INFO))


@app.callback()
def main() -> None:
    """
    DiffSage CLI entry point.
    """
    pass


app.command()(doctor)
