import typer

from diffsage.config.loader import load_settings
from diffsage.logging.logger import get_logger

logger = get_logger(__name__)

def doctor() -> None:
    """Run environment diagnostics"""

    settings = load_settings()
    
    logger.info("Running doctor command.")

    typer.echo("DiffSage Doctor")
    typer.echo(f"Provider      : {settings.provider}")
    typer.echo(f"Timeout       : {settings.timeout}")
    typer.echo(f"Max Retries   : {settings.max_retries}")
    typer.echo(f"Log Level     : {settings.log_level}")