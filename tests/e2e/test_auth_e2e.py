"""End-to-end tests for `diffsage auth`: real CLI, isolated credentials file."""

import os

import pytest
from typer.testing import CliRunner

from diffsage.cli import app
from tests.fakes import FakeProvider

runner = CliRunner()


def flat(output: str) -> str:
    """Join lines, because Rich wraps long messages such as file paths."""

    return " ".join(output.split())


@pytest.mark.skipif(os.name != "posix", reason="Unix permission bits only")
def test_auth_set_stores_key_readable_only_by_owner(isolated_env) -> None:
    result = runner.invoke(app, ["auth", "set", "gemini"], input="secret-key\n")

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
    assert stored_key(isolated_env) == "secret-key"


def test_auth_set_rejects_key_as_argument(isolated_env) -> None:
    """The key must never be accepted as an argument: it would stay in shell history and
    be visible to other processes."""

    result = runner.invoke(app, ["auth", "set", "gemini", "secret-key"])

    assert result.exit_code == 2
    assert "unexpected extra argument" in flat(result.output)
    assert stored_key(isolated_env) is None


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


def test_auth_set_help_explains_how_the_key_is_entered() -> None:
    result = runner.invoke(app, ["auth", "set", "--help"])

    assert result.exit_code == 0, result.output
    assert "hidden prompt" in flat(result.output)
    assert "never as an argument" in flat(result.output)
    assert "pipe it in" in flat(result.output)


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


@pytest.fixture
def captured_credentials(monkeypatch) -> list:
    """Record the credential each AIService builds its provider with."""

    used: list = []
    provider = FakeProvider()
    provider.queue("answer")

    def create(_settings, credential):
        used.append(credential)
        return provider

    monkeypatch.setattr("diffsage.services.ai_service.create_provider", create)
    return used


def test_ask_uses_environment_key_without_any_stored_credential(
    captured_credentials, monkeypatch
) -> None:
    monkeypatch.setenv("DIFFSAGE_API_KEY", "env-key")

    result = runner.invoke(app, ["ask", "hello"])

    assert result.exit_code == 0, result.output
    assert [credential.api_key for credential in captured_credentials] == ["env-key"]


def test_environment_key_overrides_stored_key(captured_credentials, monkeypatch) -> None:
    runner.invoke(app, ["auth", "set", "gemini"], input="stored-key\n")
    monkeypatch.setenv("DIFFSAGE_API_KEY", "env-key")

    result = runner.invoke(app, ["ask", "hello"])

    assert result.exit_code == 0, result.output
    assert captured_credentials[0].api_key == "env-key"


def test_empty_environment_key_is_reported(monkeypatch) -> None:
    runner.invoke(app, ["auth", "set", "gemini"], input="stored-key\n")
    monkeypatch.setenv("DIFFSAGE_API_KEY", "")

    result = runner.invoke(app, ["ask", "hello"])

    assert result.exit_code == 1
    assert "✗ DIFFSAGE_API_KEY is set but empty." in flat(result.output)


def test_missing_key_suggests_auth_set_or_environment_variable() -> None:
    result = runner.invoke(app, ["ask", "hello"])

    assert result.exit_code == 1
    assert "Run 'diffsage auth set gemini', or set DIFFSAGE_API_KEY." in flat(result.output)


@pytest.mark.parametrize("command", [["auth", "list"], ["auth", "get", "gemini"]])
def test_auth_commands_warn_when_environment_key_overrides(command, monkeypatch) -> None:
    runner.invoke(app, ["auth", "set", "gemini"], input="stored-key\n")
    monkeypatch.setenv("DIFFSAGE_API_KEY", "env-key")

    result = runner.invoke(app, command)

    assert result.exit_code == 0, result.output
    assert "! DIFFSAGE_API_KEY is set, so AI commands use it instead of stored" in flat(
        result.output
    )
    assert "env-key" not in result.output


@pytest.mark.parametrize("command", [["auth", "list"], ["auth", "get", "gemini"]])
def test_auth_commands_do_not_warn_without_environment_key(command) -> None:
    runner.invoke(app, ["auth", "set", "gemini"], input="stored-key\n")

    result = runner.invoke(app, command)

    assert result.exit_code == 0, result.output
    assert "DIFFSAGE_API_KEY" not in result.output


def store_profiles() -> None:
    runner.invoke(app, ["auth", "set", "gemini"], input="default-key\n")
    runner.invoke(app, ["auth", "set", "gemini", "--name", "paid"], input="paid-key\n")


def test_ai_commands_use_the_default_profile_unless_configured(captured_credentials) -> None:
    store_profiles()

    result = runner.invoke(app, ["ask", "hello"])

    assert result.exit_code == 0, result.output
    assert captured_credentials[0].api_key == "default-key"


@pytest.mark.usefixtures("git_repo")
def test_configured_credential_profile_selects_the_stored_key(captured_credentials) -> None:
    """Regression: profiles could be stored with --name but were never used."""

    store_profiles()
    runner.invoke(app, ["config", "set", "credential_profile", "Paid", "--local"])

    result = runner.invoke(app, ["ask", "hello"])

    assert result.exit_code == 0, result.output
    assert captured_credentials[0].api_key == "paid-key"


def test_environment_variable_selects_a_profile_for_one_run(
    captured_credentials, monkeypatch
) -> None:
    store_profiles()
    monkeypatch.setenv("DIFFSAGE_CREDENTIAL_PROFILE", "paid")

    result = runner.invoke(app, ["ask", "hello"])

    assert result.exit_code == 0, result.output
    assert captured_credentials[0].api_key == "paid-key"


def test_missing_profile_explains_how_to_create_it(monkeypatch) -> None:
    store_profiles()
    monkeypatch.setenv("DIFFSAGE_CREDENTIAL_PROFILE", "work")

    result = runner.invoke(app, ["ask", "hello"])

    assert result.exit_code == 1
    assert (
        "✗ Credential not found for provider 'gemini' and profile 'work'. Run 'diffsage auth "
        "set gemini --name work', or set DIFFSAGE_API_KEY." in flat(result.output)
    )


def test_config_list_shows_the_credential_profile() -> None:
    result = runner.invoke(app, ["config", "list"])

    assert result.exit_code == 0, result.output
    assert "Credential Profile" in result.output
    assert "default" in result.output


@pytest.mark.parametrize("command", [["auth", "list"], ["auth", "get", "gemini"], ["ask", "hi"]])
def test_malformed_credentials_file_is_reported_by_every_command(isolated_env, command) -> None:
    isolated_env.config_dir.mkdir(parents=True, exist_ok=True)
    (isolated_env.config_dir / "credentials.toml").write_text('[credentials]\ngemini = "my-key"\n')

    result = runner.invoke(app, command)

    assert result.exit_code == 1
    assert "'credentials.gemini' should be a table, not string" in flat(result.output)
    assert "unexpected error" not in result.output.lower()
