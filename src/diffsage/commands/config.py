import typer

from diffsage.config.loader import load_settings
from diffsage.exceptions import UnknownConfigurationKeyError
from diffsage.logging.logger import get_logger
from diffsage.services.config_service import ConfigService
from diffsage.ui.config_view import ConfigView

logger = get_logger(__name__)

app = typer.Typer(
    help="DiffSage configuration",
    invoke_without_command=False
)

@app.command("list")
def list_config() -> None:
    """List the current DiffSage configuration."""

    view = ConfigView()

    try:
        settings = load_settings()
        
        service = ConfigService(settings)

        report = service.get_configuration()
        view.show_configuration(report)

    except Exception:
        logger.exception("Unexpected error while executing config command.")
        view.show_error("An unexpected error occurred. Please check the log file for more details.")
        raise SystemExit(1) from None

@app.command("get")
def get_config(key: str) -> None:
    """Get the value of a DiffSage configuration."""

    view = ConfigView()

    try:
        settings = load_settings()

        service = ConfigService(settings)

        report = service.get_value(key.strip().lower())
        view.show_value(report)

    except UnknownConfigurationKeyError as e:
        logger.warning(str(e))
        view.show_error(str(e))
        raise SystemExit(1) from None

    except Exception:
        logger.exception("Unexpected error while executing config command.")
        view.show_error("An unexpected error occurred. Please check the log file for more details.")
        raise SystemExit(1) from None