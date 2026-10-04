from pathlib import Path

from rich.panel import Panel
from rich.table import Table

from diffsage.config.paths import display_path
from diffsage.models.config import ConfigReport, ConfigSources, ConfigValueReport, RawConfigReport
from diffsage.ui.base import BaseView


class ConfigView(BaseView):
    """Handles terminal rendering for the config command."""

    def _display_value(self, value: str | int | None) -> str:
        if value is None:
            return "None"

        return str(value)

    def show_configuration(self, report: ConfigReport | RawConfigReport) -> None:
        table = Table(show_header=False, box=False, expand=False)

        table.add_row("Provider", self._display_value(report.provider))
        table.add_row("Model", self._display_value(report.model))
        table.add_row("Credential Profile", self._display_value(report.credential_profile))
        table.add_row("Timeout", self._display_value(report.timeout))
        table.add_row("Max Retries", self._display_value(report.max_retries))
        table.add_row("Log Level", self._display_value(report.log_level))

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
                self._display_value(report.value),
                title=f"[bold cyan]{report.key.replace('_', ' ').title()}[/bold cyan]",
                expand=False,
            )
        )

    def show_success(self, message: str) -> None:
        self._console.print()
        self._console.print(f"[bold green]✓ {message}[bold green]")
        self._console.print()

    def show_sources(self, sources: ConfigSources) -> None:
        table = Table(show_header=False, box=None, expand=False, padding=(0, 2, 0, 0))
        table.add_column(no_wrap=True)
        # Paths wrap instead of being truncated with "…", so they can always be read in full.
        table.add_column(overflow="fold")

        table.add_row("defaults", "built-in")

        if sources.global_file is not None:
            table.add_row("global", display_path(sources.global_file))

        if sources.local_file is not None:
            table.add_row("local", display_path(sources.local_file))

        if sources.environment:
            table.add_row("environment", ", ".join(sources.environment))

        self._console.print("[dim]Sources (later entries override earlier ones):[/]")
        self._console.print(table)
        self._console.print()

    def show_path(self, path: Path) -> None:
        display = str(path).replace(str(Path.home()), "~")

        self._console.print("[dim]Location:[/]")
        self._console.print(
            f"[cyan]{display}[/]",
            no_wrap=True,
        )
        self._console.print()
