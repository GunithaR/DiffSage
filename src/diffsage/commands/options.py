"""Command-line options shared by commands that generate something for review."""

import sys
from typing import Annotated

import typer

from diffsage.exceptions import NoTerminalError

YES_HELP = "Accept the generated result without asking (for scripts and CI)."
DRY_RUN_HELP = "Show the generated result without applying it, and without asking."

# Annotated keeps a plain False default, so the commands can also be called as ordinary
# functions (tests do); `= typer.Option(False, ...)` would make the default a truthy object.
YesOption = Annotated[bool, typer.Option("--yes", "-y", help=YES_HELP)]
DryRunOption = Annotated[bool, typer.Option("--dry-run", help=DRY_RUN_HELP)]


def stdin_is_terminal() -> bool:
    return sys.stdin.isatty()


def check_yes_and_dry_run(*, yes: bool, dry_run: bool, command: str, action: str) -> None:
    """Reject option combinations that cannot work, before anything is generated.

    --yes applies the result and --dry-run never applies it, so they cannot be combined.
    Without either, the command asks before `action`; with no terminal to ask in (CI,
    git hooks, pipes) it would otherwise spend an AI request and then fail, or hang
    waiting for an answer that never comes.
    """

    if yes and dry_run:
        raise typer.BadParameter(
            "--yes and --dry-run cannot be used together.", param_hint="'--yes' / '--dry-run'"
        )

    if not (yes or dry_run) and not stdin_is_terminal():
        raise NoTerminalError(
            f"diffsage {command} needs a terminal to ask before {action}. In scripts and CI, "
            f"add --yes to go ahead without asking, or --dry-run to only show the result."
        )
