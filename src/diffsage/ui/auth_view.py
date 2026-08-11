from rich.panel import Panel
from rich.table import Table

from diffsage.models.credentials import Credential
from diffsage.ui.base import BaseView


class AuthView(BaseView):
    """Handles terminal rendering for the auth command."""

    def show_success(self, message: str) -> None:
        self._console.print(f"[bold green]✓ {message}[bold green]")

    def show_credential(self, credential: Credential) -> None:
        table = Table(show_header=False, box=False, expand=False)

        table.add_row("Provider", credential.provider)
        table.add_row("Profile", credential.name)
        table.add_row("API Key", self._mask_api_key(credential.api_key))

        self._console.print(
            Panel(
                table,
                title="[bold cyan]DiffSage Credential[/bold cyan]",
                expand=False,
            )
        )

    def show_credentials(self, credentials: list[Credential]) -> None:
        table = Table(show_header=False, box=False, expand=False)

        for credential in credentials:
            table.add_row(
                credential.provider,
                credential.name,
            )

        self._console.print(
            Panel(
                table,
                title="[bold cyan]DiffSage Credential[/bold cyan]",
                expand=False,
            )
        )

    @staticmethod
    def _mask_api_key(api_key: str) -> str:
        if len(api_key) <= 8:
            return "••••••••"

        return f"{api_key[:4]}••••••••{api_key[-4:]}"
