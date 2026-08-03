from rich.console import Console

from diffsage.models.provider import ProviderResponse
from diffsage.ui.base import BaseView


class AskView(BaseView):
    """Handles terminal rendering for the ask command."""

    def __init__(self) -> None:
        self._console = Console()


    def show_response(self, response: ProviderResponse):
        self._console.print(f"[green]{response.content}[/green]")
        self._console.print()
