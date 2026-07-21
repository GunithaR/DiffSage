import typer

from diffsage.logging.logger import get_logger
from diffsage.services.doctor_service import DoctorService

logger = get_logger(__name__)


def status_icon(status: bool) -> str:
    """Return a status icon for terminal output."""
    return "✓" if status else "✗"


def doctor() -> None:
    """Run environment diagnostics"""

    logger.info("Running doctor command.")

    service = DoctorService()
    report = service.run()

    typer.echo()
    typer.echo("DiffSage Doctor")
    typer.echo()

    typer.echo(f"{status_icon(True)} Python Version : {report.python_version}")
    typer.echo(
        f"{status_icon(report.git_installed)} Git Installed  : {report.git_version or 'Not Found'}"
    )

    virtual_env_status = "Active" if report.virtual_environment else "Inactive"
    typer.echo(f"{status_icon(report.virtual_environment)} Virtual Env.   : {virtual_env_status}")

    typer.echo(
        f"{status_icon(report.configuration_loaded)} Configuration  : {report.configuration_loaded}"
    )

    typer.echo()

    typer.echo(f"Provider       : {report.provider}")
    typer.echo(f"Timeout        : {report.timeout}")
    typer.echo(f"Max Retries    : {report.max_retries}")
    typer.echo(f"Log Level      : {report.log_level}")
