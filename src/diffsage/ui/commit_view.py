from contextlib import contextmanager

from rich.console import Group
from rich.panel import Panel
from rich.rule import Rule
from rich.table import Table
from rich.text import Text

from diffsage.models.commit_message import CommitMessage
from diffsage.ui.base import BaseView


class CommitView(BaseView):
    """Handles terminal rendering for the commit command."""

    @contextmanager
    def generating(self):
        with self._console.status("Generating commit message...") as status:
            yield status

    def show_generated(self) -> None:
        self._console.print("[green]✓ Commit message generated successfully.[/green]")

    def show_not_git_repository(self):
        self._console.print("[red]Not inside a Git repository[/red]")

    def show_no_staged_changes(self):
        self._console.print("[yellow]No staged changes found[/yellow]")

    def show_commit(self, message: CommitMessage) -> None:
        grid = Table.grid(expand=True)
        grid.add_column(style="cyan", width=10)
        grid.add_column()

        if message.type:
            grid.add_row("Type", message.type)

        if message.scope:
            grid.add_row("Scope", message.scope)

        if message.breaking:
            grid.add_row("Breaking", "[bold yellow]yes[/bold yellow]")

        grid.add_row("Subject", message.subject)

        body = Text()

        if message.body:
            for i, line in enumerate(message.body):
                line = line.strip()
                if not line:
                    continue

                if line.startswith("- "):
                    line = line.removeprefix("- ")

                body.append(f"• {line}")
                if i < len(message.body) - 1:
                    body.append("\n")

            content = Group(
                grid,
                Rule(style="cyan"),
                body,
            )
            panel = Panel(
                content,
                title="[bold cyan]Commit Message[/bold cyan]",
                expand=False,
            )
        else:
            panel = Panel(
                grid,
                title="[bold cyan]Suggested Commit Message[/bold cyan]",
                expand=False,
            )

        self._console.print()
        self._console.print(panel)

    def prompt_action(self) -> str:
        self._console.print()

        return self._console.input(
            "[bold cyan][Y][/bold cyan] Commit (default)   "
            "[bold cyan][E][/bold cyan] Edit   "
            "[bold cyan][R][/bold cyan] Regenerate   "
            "[bold cyan][N][/bold cyan] Cancel:  "
        )

    def show_success(self, message: str) -> None:
        self._console.print()
        self._console.print("[bold green]✓ Commit created successfully.[/bold green]")
        self._console.print()
        self._console.print("[dim]Commit:[/dim]")
        self._console.print(message)
        self._console.print()

    def show_cancelled(self) -> None:
        self._console.print("[yellow]Cancelled.[/yellow]")

    def show_invalid_option(self) -> None:
        self._console.print("[red]Invalid option. Please choose Y, E, R or N.[/red]")
