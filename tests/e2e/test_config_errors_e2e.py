"""End-to-end tests for how the CLI reports a broken configuration file."""

import pytest
from typer.testing import CliRunner

from diffsage.cli import app

runner = CliRunner()


def flat(output: str) -> str:
    """Join lines, because Rich wraps long messages such as file paths."""

    return " ".join(output.split())


@pytest.fixture
def broken_global_config(isolated_env):
    path = isolated_env.config_dir / "config.toml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('[network]\ntimeout = "abc"\n')
    return path


@pytest.mark.usefixtures("broken_global_config")
def test_invalid_value_is_reported_without_traceback() -> None:
    """Regression: a wrong-typed value crashed every command with a pydantic traceback."""

    result = runner.invoke(app, ["ask", "hello"])

    assert result.exit_code == 1
    assert "✗ Invalid configuration in" in flat(result.output)
    assert "network.timeout: Input should be a valid integer" in flat(result.output)
    assert "Traceback" not in result.output
    assert "ValidationError" not in result.output


def test_invalid_toml_is_reported_with_position(broken_global_config) -> None:
    """Regression: a TOML syntax error escaped the startup callback as a traceback."""

    broken_global_config.write_text("[network\ntimeout = 5\n")

    result = runner.invoke(app, ["ask", "hello"])

    assert result.exit_code == 1
    assert "✗ Invalid TOML syntax in" in flat(result.output)
    assert "line 1" in flat(result.output)
    assert "Traceback" not in result.output


@pytest.mark.usefixtures("broken_global_config")
def test_version_works_with_broken_config() -> None:
    result = runner.invoke(app, ["--version"])

    assert result.exit_code == 0


def test_config_unset_can_repair_broken_config(broken_global_config) -> None:
    """Regression: the startup callback blocked `config unset` from fixing the file."""

    result = runner.invoke(app, ["config", "unset", "timeout", "--global"])

    assert result.exit_code == 0, result.output
    assert "timeout" not in broken_global_config.read_text()


def test_config_set_repairs_broken_value(broken_global_config) -> None:
    result = runner.invoke(app, ["config", "set", "timeout", "45", "--global"])

    assert result.exit_code == 0, result.output
    assert "timeout = 45" in broken_global_config.read_text()

    resolved = runner.invoke(app, ["config", "get", "timeout"])
    assert resolved.exit_code == 0, resolved.output
    assert "45" in resolved.output


def test_partial_repair_saves_change_and_reports_remaining_problem(broken_global_config) -> None:
    broken_global_config.write_text('[network]\ntimeout = "abc"\nmax_retries = "x"\n')

    result = runner.invoke(app, ["config", "unset", "timeout", "--global"])

    assert result.exit_code == 1
    assert "✗ Configuration updated, but it is still invalid:" in flat(result.output)
    assert "network.max_retries" in flat(result.output)
    assert "timeout" not in broken_global_config.read_text()


@pytest.mark.usefixtures("broken_global_config")
def test_config_list_global_shows_raw_file_values() -> None:
    result = runner.invoke(app, ["config", "list", "--global"])

    assert result.exit_code == 0, result.output
    assert "abc" in result.output


@pytest.mark.usefixtures("broken_global_config")
def test_resolved_config_view_still_reports_the_error() -> None:
    result = runner.invoke(app, ["config", "list"])

    assert result.exit_code == 1
    assert "✗ Invalid configuration in" in flat(result.output)


@pytest.mark.usefixtures("broken_global_config")
def test_doctor_reports_broken_config_instead_of_crashing() -> None:
    result = runner.invoke(app, ["doctor"])

    assert result.exit_code == 0, result.output
    assert "✗ Configuration : Invalid configuration in" in flat(result.output)
    assert "Built-in defaults are shown below" in result.output
    assert "Timeout : 30" in flat(result.output)


@pytest.mark.usefixtures("isolated_env")
def test_doctor_reports_loaded_config() -> None:
    result = runner.invoke(app, ["doctor"])

    assert result.exit_code == 0, result.output
    assert "✓ Configuration : Loaded" in flat(result.output)
    assert "Built-in defaults are shown below" not in result.output


@pytest.mark.usefixtures("broken_global_config", "git_repo")
def test_other_commands_still_stop_on_broken_config() -> None:
    result = runner.invoke(app, ["commit"])

    assert result.exit_code == 1
    assert "✗ Invalid configuration in" in flat(result.output)


UNQUOTED_VALUE = "[network]\nmax_retries = 3\ntimeout = abc\n"


@pytest.mark.parametrize(
    "command",
    [
        ["config", "set", "timeout", "60", "--local"],
        ["config", "unset", "timeout", "--local"],
        ["config", "list", "--local"],
    ],
)
def test_local_toml_syntax_error_is_reported_not_unexpected(git_repo, command) -> None:
    """Regression: an unquoted value in .diffsage.toml made `config set --local` report an
    unexpected error, because the write path's TOML parser error was not caught."""

    local_config = git_repo / ".diffsage.toml"
    local_config.write_text(UNQUOTED_VALUE)

    result = runner.invoke(app, command)

    assert result.exit_code == 1
    assert "✗ Invalid TOML syntax in" in flat(result.output)
    assert "line 3" in flat(result.output)
    assert "fix that line in a text editor" in flat(result.output)
    assert "unexpected error" not in result.output.lower()
    assert local_config.read_text() == UNQUOTED_VALUE


def test_doctor_reports_local_toml_syntax_error(git_repo) -> None:
    (git_repo / ".diffsage.toml").write_text(UNQUOTED_VALUE)

    result = runner.invoke(app, ["doctor"])

    assert result.exit_code == 0, result.output
    assert "✗ Configuration : Invalid TOML syntax in" in flat(result.output)
