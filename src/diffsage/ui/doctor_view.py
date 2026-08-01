import typer

from diffsage.models.doctor_report import DoctorReport


class DoctorView:

    def _status_icon(self, status: bool) -> str:
        """Return a status icon for terminal output."""

        return "✓" if status else "✗"

    def show_report(self, report: DoctorReport) -> None:
        typer.echo()
        typer.echo("DiffSage Doctor")
        typer.echo()
    
        typer.echo(f"{self._status_icon(True)} Python Version : {report.python_version}")

        git_version = report.git_version or "Not Found"
        typer.echo(
            f"{self._status_icon(report.git_installed)} Git Installed  : {git_version}"
        )
    
        virtual_env_status = "Active" if report.virtual_environment else "Inactive"
        typer.echo(
            f"{self._status_icon(report.virtual_environment)} "
            f"Virtual Env.   : {virtual_env_status}"
        )
    
        typer.echo(
            f"{self._status_icon(report.configuration_loaded)} "
            f"Configuration  : {report.configuration_loaded}"
        )
    
        typer.echo()
    
        typer.echo(f"Provider       : {report.provider}")
        typer.echo(f"Timeout        : {report.timeout}")
        typer.echo(f"Max Retries    : {report.max_retries}")
        typer.echo(f"Log Level      : {report.log_level}")