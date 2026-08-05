import typer

from diffsage.config.loader import load_settings
from diffsage.config.resolver import get_local_config_path
from diffsage.exceptions import InvalidConfigurationValueError, UnknownConfigurationKeyError
from diffsage.logging.logger import get_logger
from diffsage.services.config_service import ConfigService
from diffsage.storage.config_repository import ConfigRepository
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

        path = get_local_config_path()
        repository = ConfigRepository(path)

        service = ConfigService(settings, repository)

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

        path = get_local_config_path()
        repository = ConfigRepository(path)

        service = ConfigService(settings, repository)

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

@app.command("set")
def set_config(key: str, value: str) -> None:
    """Set the value of a DiffSage configuration."""

    view = ConfigView()

    try: 
        settings = load_settings()

        path = get_local_config_path()
        repository = ConfigRepository(path)

        service = ConfigService(settings, repository)

        report = service.set_value(key, value)

        view.show_success("Configuration updated.")
        view.show_configuration(report)

    except UnknownConfigurationKeyError as e:
        logger.warning(str(e))
        view.show_error(str(e))
        raise SystemExit(1) from None

    except InvalidConfigurationValueError as e:
        logger.warning(str(e))
        view.show_error(str(e))
        raise SystemExit(1) from None

    except Exception:
        logger.exception("Unexpected error while executing config command.")
        view.show_error("An unexpected error occurred. Please check the log file for more details.")
        raise SystemExit(1) from None

@app.command("unset")
def unset_config(key: str) -> None:
    """Remove a DiffSage configuration value."""

    view = ConfigView()

    try:
        settings = load_settings()

        path = get_local_config_path()
        repository = ConfigRepository(path)

        service = ConfigService(settings, repository)

        report = service.unset_value(key)

        view.show_success("Configuration deleted.")
        view.show_configuration(report)

    except UnknownConfigurationKeyError as e:
        logger.warning(str(e))
        view.show_error(str(e))
        raise SystemExit(1) from None

    except Exception:
        logger.exception("Unexpected error while executing config command.")
        view.show_error("An unexpected error occurred. Please check the log file for more details.")
        raise SystemExit(1) from None