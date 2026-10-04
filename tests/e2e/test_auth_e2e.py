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
