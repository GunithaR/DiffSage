import functools
from collections.abc import Callable

import typer

from diffsage.exceptions import DiffSageError
from diffsage.logging.logger import get_logger
from diffsage.ui.base import BaseView

logger = get_logger(__name__)

UNEXPECTED_ERROR_MESSAGE = (
    "An unexpected error occurred. Please check the log file for more details."
)


def handle_command_errors[**P, R](
    command: str,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Turn errors raised by a CLI command into a message and an exit status.

    - DiffSageError: its message is shown and the process exits with its exit_code.
    - Typer control flow (Exit, Abort, BadParameter): passed through untouched, so
      --help, --version and argument validation keep working. Typer vendors its own
      copy of Click, so these must be Typer's classes, not the `click` package's.
    - Anything else: logged with a traceback and reported as an unexpected error.
    """

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            view = BaseView()

            try:
                return func(*args, **kwargs)

            except (typer.Exit, typer.Abort, typer.BadParameter):
                raise

            except DiffSageError as error:
                logger.warning("%s command failed: %s", command, error.message)
                view.show_error(error.message)
                raise SystemExit(error.exit_code) from None

            except Exception:
                logger.exception("Unexpected error while executing %s command.", command)
                view.show_error(UNEXPECTED_ERROR_MESSAGE)
                raise SystemExit(1) from None

        return wrapper

    return decorator
