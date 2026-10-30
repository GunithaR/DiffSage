"""Command-line options shared by commands that generate something for review."""

from typing import Annotated

import typer

YES_HELP = "Accept the generated result without asking (for scripts and CI)."
DRY_RUN_HELP = "Show the generated result without applying it, and without asking."

# Annotated keeps a plain False default, so the commands can also be called as ordinary
# functions (tests do); `= typer.Option(False, ...)` would make the default a truthy object.
YesOption = Annotated[bool, typer.Option("--yes", "-y", help=YES_HELP)]
DryRunOption = Annotated[bool, typer.Option("--dry-run", help=DRY_RUN_HELP)]


def check_yes_and_dry_run(*, yes: bool, dry_run: bool) -> None:
    """--yes applies the result and --dry-run never applies it, so they cannot be combined."""

    if yes and dry_run:
        raise typer.BadParameter(
            "--yes and --dry-run cannot be used together.", param_hint="'--yes' / '--dry-run'"
        )
