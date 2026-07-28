from rich.console import Console
from contextlib import contextmanager

console = Console()


class CommitView:
    """Handles terminal rendering for the commit command."""

    def __init__(self) -> None:
        self._console = Console()

    @contextmanager
    def generating(self):
        with self._console.status("Generating commit message..."):
            yield 

    def show_commit(self, message: str) -> None:
        console.print()
        console.print("[green]Suggested commit message:[/green]")
        console.print(message)

        


    