import typer

from diffsage.commands.doctor import doctor

app = typer.Typer(
    help="DiffSage: AI-powered Git workflow assistant."
)

@app.callback() 
def main() -> None:
    """
    DiffSage CLI entry point.
    """
    pass

app.command()(doctor)