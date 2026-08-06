from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from pathlib import Path

from diffsage.models.config import ConfigReport, ConfigValueReport
from diffsage.ui.base import BaseView


class ConfigView(BaseView):
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

    def show_value(self, report: ConfigValueReport) -> None:
        self._console.print(
            Panel(
                report.value,
                title=f"[bold cyan]{report.key.replace("_", " ").title()}[/bold cyan]",
                expand=False
            )
        )

    def show_success(self, message: str) -> None:
        self._console.print()
        self._console.print(f"[bold green]✓ {message}[bold green]")
        self._console.print()


    def show_path(self, path: Path) -> None:
        display = str(path).replace(str(Path.home()), "~")

        self._console.print("[dim]Location:[/]")
        self._console.print(
            f"[cyan]{display}[/]",
            no_wrap=True,
        )
        self._console.print()
