from rich.console import Console
from rich.panel import Panel
from contextlib import contextmanager


class CommitView:
    """Handles terminal rendering for the commit command."""

    def __init__(self) -> None:
        self._console = Console()

    @contextmanager
    def generating(self):
        with self._console.status("Generating commit message..."):
            yield 

    def show_commit(self, message: str) -> None:
        panel = Panel(
            message,
            title="[bold cyan]Suggested Commit Message[/bold cyan]",
            expand=False,
        )
        self._console.print()
        self._console.print(panel)

    def prompt_action(self) -> str: 
        self._console.print()

        return self._console.input(
                    "[bold cyan][Y][/bold cyan] Commit  "
                    "[bold cyan][E][/bold cyan] Edit  "
                    "[bold cyan][R][/bold cyan] Regenerate  "
                    "[bold cyan][N][/bold cyan] Cancel: "
        )

    def show_success(self, message: str) -> None:
        self._console.print(
            f"[bold green]✓ Commit created successfully![/bold green] {message.splitlines()[0]}"
        )

    def show_cancelled(self) -> None:
        self._console.print("[yellow]Cancelled.[/yellow]")

    def show_invalid_option(self) -> None:
        self._console.print("[red]Invalid option. Please choose Y, E, R or N.[/red]")

    def show_not_git_repository(self):
        self._console.print("[red]Not inside a Git repository[/red]")

    def show_no_staged_changes(self):
        self._console.print("[yellow]No staged changes found[/yellow]")

    def show_generated(self) -> None:
        self._console.print()
        self._console.print("[green]✓ Commit message generated[/green]")


 

        


    