import os
import platform
import shutil
import subprocess

from diffsage.config.loader import load_settings
from diffsage.logging.logger import get_logger
from diffsage.models.doctor_report import DoctorReport

logger = get_logger(__name__)


class DoctorService:
    """Runs environment diagnostics."""

    def run(self) -> DoctorReport:
        logger.info("Loading application settings.")

        settings = load_settings()

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
            configuration_loaded=True,
        )
