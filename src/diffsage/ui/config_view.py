from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from diffsage.models.config_report import ConfigReport


class ConfigView:
    """Handles terminal rendering for the config command."""

    def __init__(self) -> None:
        self._console = Console()

    def show_configuration(self, report: ConfigReport) -> None:
        table = Table(show_header=False, box=False, expand=False)

        table.add_row("Provider", report.provider)
        table.add_row("Model", report.model)
        table.add_row("Timeout", str(report.timeout))
        table.add_row("Max Retries", str(report.max_retries))
        table.add_row("Log Level", report.log_level)

        self._console.print(
            Panel(
                table,
                title="[bold cyan]DiffSage Configuration[/bold cyan]",
                expand=False,
            )
        )