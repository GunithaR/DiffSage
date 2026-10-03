import os
import platform
import shutil
import subprocess

from diffsage.config.loader import default_settings, load_settings
from diffsage.exceptions import ConfigError
from diffsage.logging.logger import get_logger
from diffsage.models.doctor import DoctorReport

logger = get_logger(__name__)


class DoctorService:
    """Runs environment diagnostics."""

    def run(self) -> DoctorReport:
        logger.info("Loading application settings.")

        configuration_error = None

        try:
            settings = load_settings()
        except ConfigError as error:
            logger.warning("Configuration could not be loaded: %s", error.message)
            configuration_error = error.message
            settings = default_settings()

        git_path = shutil.which("git")
        git_installed = git_path is not None
        git_version = None

        if git_installed:
            try:
                result = subprocess.run(
                    ["git", "--version"],
                    capture_output=True,
                    text=True,
                    check=True,
                )
                git_version = result.stdout.strip()
            except subprocess.SubprocessError:
                git_version = None

        return DoctorReport(
            python_version=platform.python_version(),
            git_installed=git_installed,
            git_version=git_version,
            provider=settings.provider,
            timeout=settings.timeout,
            max_retries=settings.max_retries,
            log_level=settings.log_level,
            virtual_environment=os.getenv("VIRTUAL_ENV") is not None,
            configuration_loaded=configuration_error is None,
            configuration_error=configuration_error,
        )
