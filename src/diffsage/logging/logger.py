import logging
from pathlib import Path

_CONFIGURED = False


def configure_logging(level: int = logging.INFO) -> None:
    """Configure the application's logging."""

    global _CONFIGURED

    if _CONFIGURED:
        return

    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    log_directory = Path("logs")
    log_directory.mkdir(exist_ok=True)
    log_file = log_directory / "diffsage.log"

    console_handler = logging.StreamHandler()
    file_handler = logging.FileHandler(log_file)

    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")

    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)

    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

    _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    """Return a logger."""

    return logging.getLogger(name)
