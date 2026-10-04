"""End-to-end tests for `diffsage auth`: real CLI, isolated credentials file."""

import os

import pytest
from typer.testing import CliRunner

from diffsage.cli import app

runner = CliRunner()


def flat(output: str) -> str:
    """Join lines, because Rich wraps long messages such as file paths."""

    return " ".join(output.split())


@pytest.mark.skipif(os.name != "posix", reason="Unix permission bits only")
def test_auth_set_stores_key_readable_only_by_owner(isolated_env) -> None:
    result = runner.invoke(app, ["auth", "set", "gemini", "secret-key"])

    assert result.exit_code == 0, result.output
    path = isolated_env.config_dir / "credentials.toml"
    assert path.stat().st_mode & 0o777 == 0o600


def test_auth_reports_unparseable_credentials_file(isolated_env) -> None:
    isolated_env.config_dir.mkdir(parents=True, exist_ok=True)
    (isolated_env.config_dir / "credentials.toml").write_text("[credentials\n")

    result = runner.invoke(app, ["auth", "list"])

    assert result.exit_code == 1
    assert "✗ Invalid TOML syntax in" in flat(result.output)
    assert "unexpected error" not in result.output.lower()


def stored_key(isolated_env) -> str | None:
    path = isolated_env.config_dir / "credentials.toml"
    if not path.exists():
        return None
    for line in path.read_text().splitlines():
        if line.startswith("api_key"):
            return line.split("=", 1)[1].strip().strip('"')
    return None


@pytest.fixture
def terminal(monkeypatch) -> None:
    """Make DiffSage treat stdin as an interactive terminal (CliRunner pipes it)."""

    monkeypatch.setattr("diffsage.commands.auth._stdin_is_terminal", lambda: True)


@pytest.mark.usefixtures("terminal")
def test_auth_set_without_key_prompts_with_hidden_input(isolated_env) -> None:
    result = runner.invoke(app, ["auth", "set", "gemini"], input="secret-key\n")

    assert result.exit_code == 0, result.output
    assert "API key for gemini:" in result.output
    assert "secret-key" not in result.output
    assert "command line" not in result.output
    assert stored_key(isolated_env) == "secret-key"


def test_auth_set_with_key_argument_warns_but_still_saves(isolated_env) -> None:
    result = runner.invoke(app, ["auth", "set", "gemini", "secret-key"])

    assert result.exit_code == 0, result.output
    assert "! The API key was passed on the command line" in flat(result.output)
    assert "run 'diffsage auth set gemini' and enter it when prompted" in flat(result.output)
    assert stored_key(isolated_env) == "secret-key"


@pytest.mark.usefixtures("terminal")
def test_auth_set_prompt_asks_again_after_empty_input(isolated_env) -> None:
    result = runner.invoke(app, ["auth", "set", "gemini"], input="\nsecret-key\n")

    assert result.exit_code == 0, result.output
    assert result.output.count("API key for gemini:") == 2
    assert stored_key(isolated_env) == "secret-key"


@pytest.mark.usefixtures("terminal")
def test_auth_set_without_any_input_saves_nothing(isolated_env) -> None:
    result = runner.invoke(app, ["auth", "set", "gemini"], input="")

    assert result.exit_code == 1
    assert "Aborted" in result.output
    assert stored_key(isolated_env) is None


def test_auth_set_help_explains_leaving_the_key_out() -> None:
    result = runner.invoke(app, ["auth", "set", "--help"])

    assert result.exit_code == 0, result.output
    assert "Leave it out to enter it at a hidden prompt" in flat(result.output)


def test_auth_set_reads_piped_key_without_prompt_or_warning(isolated_env) -> None:
    """Regression: piped input went through getpass, which printed a misleading
    "Password input may be echoed" warning."""

    result = runner.invoke(app, ["auth", "set", "gemini"], input="piped-key\n")

    assert result.exit_code == 0, result.output
    assert "API key for gemini" not in result.output
    assert "echo" not in result.output.lower()
    assert "piped-key" not in result.output
    assert stored_key(isolated_env) == "piped-key"


def test_auth_set_with_empty_pipe_saves_nothing(isolated_env) -> None:
    result = runner.invoke(app, ["auth", "set", "gemini"], input="\n")

    assert result.exit_code == 1
    assert "✗ No API key was received on standard input." in result.output
    assert stored_key(isolated_env) is None
