from rich.console import Console


class BaseView:

    def __init__(self) -> None:
        self._console = Console()

    def show_error(self, message: str) -> None:
        self._console.print(f"[red]✗ {message}[/red]")

    def show_warning(self, message: str) -> None:
        self._console.print(f"[yellow]! {message}[/yellow]")

    def show_info(self, message: str) -> None:
        self._console.print(message)