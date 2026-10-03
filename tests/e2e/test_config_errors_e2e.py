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


@pytest.mark.xfail(
    strict=True,
    reason="Bug: the startup callback loads settings before every command, so `config "
    "unset` cannot repair a broken config. Fixed by the next item on this branch.",
)
def test_config_unset_can_repair_broken_config(broken_global_config) -> None:
    result = runner.invoke(app, ["config", "unset", "timeout", "--global"])

    assert result.exit_code == 0, result.output
    assert "timeout" not in broken_global_config.read_text()
