import inspect
import logging

import pytest
import typer
from typer.testing import CliRunner

from diffsage.commands.error_handler import UNEXPECTED_ERROR_MESSAGE, handle_command_errors
from diffsage.exceptions import (
    CredentialNotFoundError,
    DiffSageError,
    NotGitRepositoryError,
    RateLimitError,
)

runner = CliRunner()


class CustomExitError(DiffSageError):
    exit_code = 3


def make_app(command) -> typer.Typer:
    app = typer.Typer()
    app.command()(command)
    # A second command keeps Typer from collapsing the app into a single command.
    app.command("noop")(lambda: None)
    return app


def invoke(command, *args: str):
    return runner.invoke(make_app(command), [command.__name__, *args])


def test_returns_command_result_when_no_error() -> None:
    @handle_command_errors("demo")
    def demo() -> str:
        return "done"

    assert demo() == "done"


def test_preserves_command_signature_for_typer() -> None:
    def demo(name: str, count: int = typer.Option(1, "--count")) -> None:
        """Demo command."""

    wrapped = handle_command_errors("demo")(demo)

    assert inspect.signature(wrapped) == inspect.signature(demo)
    assert wrapped.__doc__ == "Demo command."


def test_preserved_signature_still_parses_arguments() -> None:
    @handle_command_errors("greet")
    def greet(name: str, shout: bool = typer.Option(False, "--shout")) -> None:
        typer.echo(name.upper() if shout else name)

    result = invoke(greet, "ada", "--shout")

    assert result.exit_code == 0, result.output
    assert result.output.strip() == "ADA"


@pytest.mark.parametrize(
    ("error", "expected"),
    [
        (NotGitRepositoryError(), "Not inside a Git repository."),
        (RateLimitError("Gemini API rate limit exceeded."), "Gemini API rate limit exceeded."),
        (
            CredentialNotFoundError("gemini"),
            "Credential not found for provider 'gemini' and profile 'default'.",
        ),
    ],
)
def test_diffsage_error_shows_message_and_exits_1(error, expected) -> None:
    @handle_command_errors("fail")
    def fail() -> None:
        raise error

    result = invoke(fail)

    assert result.exit_code == 1
    assert result.output.strip() == f"✗ {expected}"


def test_diffsage_error_uses_its_exit_code() -> None:
    @handle_command_errors("fail")
    def fail() -> None:
        raise CustomExitError("custom")

    result = invoke(fail)

    assert result.exit_code == 3


def test_diffsage_error_is_logged_as_warning(caplog) -> None:
    @handle_command_errors("fail")
    def fail() -> None:
        raise NotGitRepositoryError()

    with caplog.at_level(logging.WARNING):
        invoke(fail)

    assert "fail command failed: Not inside a Git repository." in caplog.text


def test_unexpected_error_shows_generic_message_and_logs_traceback(caplog) -> None:
    @handle_command_errors("crash")
    def crash() -> None:
        raise KeyError("secret detail")

    with caplog.at_level(logging.ERROR):
        result = invoke(crash)

    assert result.exit_code == 1
    assert result.output.strip() == f"✗ {UNEXPECTED_ERROR_MESSAGE}"
    assert "secret detail" not in result.output
    assert "Unexpected error while executing crash command." in caplog.text
    assert caplog.records[-1].exc_info is not None


def test_typer_exit_passes_through() -> None:
    @handle_command_errors("leave")
    def leave() -> None:
        typer.echo("bye")
        raise typer.Exit(code=0)

    result = invoke(leave)

    assert result.exit_code == 0
    assert result.output.strip() == "bye"


def test_typer_abort_passes_through() -> None:
    @handle_command_errors("stop")
    def stop() -> None:
        raise typer.Abort()

    result = invoke(stop)

    assert result.exit_code == 1
    assert UNEXPECTED_ERROR_MESSAGE not in result.output
    assert "Aborted" in result.output


def test_usage_errors_pass_through_to_click() -> None:
    @handle_command_errors("check")
    def check() -> None:
        raise typer.BadParameter("Cannot specify both --local and --global.")

    result = invoke(check)

    assert result.exit_code == 2
    assert "Cannot specify both --local and --global." in result.output
    assert UNEXPECTED_ERROR_MESSAGE not in result.output


def test_bare_diffsage_errors_have_default_messages() -> None:
    assert str(NotGitRepositoryError()) == "Not inside a Git repository."
    assert str(DiffSageError()) == "DiffSage could not complete the command."
    assert str(NotGitRepositoryError("Custom text.")) == "Custom text."
