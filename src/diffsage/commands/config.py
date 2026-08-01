import typer

from diffsage.config.loader import load_settings
from diffsage.services.config_service import ConfigService
from diffsage.ui.config_view import ConfigView

app = typer.Typer(
    help="DiffSage Configuration",
    invoke_without_command=True)

@app.command("list")
def list_config() -> None:
    """List the current DiffSage configuration."""

    settings = load_settings()
    
    service = ConfigService(settings)
    view = ConfigView()

    report = service.get_configuration()

    view.show_configuration(report)