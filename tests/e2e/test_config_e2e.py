"""End-to-end tests for `diffsage config`: real CLI, isolated config files."""

from pathlib import Path

import pytest
from typer.testing import CliRunner

from diffsage.cli import app

runner = CliRunner()


def flat(output: str) -> str:
    """Join lines, because Rich wraps long messages such as file paths."""

    return " ".join(output.split())


@pytest.fixture
def outside_repository(tmp_path, monkeypatch) -> Path:
    directory = tmp_path / "not-a-repo"
    directory.mkdir()
    monkeypatch.chdir(directory)

    return directory


@pytest.mark.usefixtures("isolated_env", "outside_repository")
def test_config_set_local_outside_repository_explains_the_problem() -> None:
    """Regression: --local outside a repository crashed on a None path."""

    result = runner.invoke(app, ["config", "set", "model", "some-model", "--local"])

    assert result.exit_code == 1
    assert "unexpected error" not in result.output.lower()
    assert "repository" in result.output.lower()


@pytest.mark.usefixtures("isolated_env", "outside_repository")
def test_config_get_outside_repository_does_not_print_none_location() -> None:
    """Regression: the resolved view printed 'Location: None' outside a repository."""

    result = runner.invoke(app, ["config", "get", "model"])

    assert result.exit_code == 0, result.output
    assert "None" not in result.output


@pytest.mark.usefixtures("outside_repository")
def test_config_set_local_outside_repository_shows_the_full_reason() -> None:
    result = runner.invoke(app, ["config", "set", "model", "some-model", "--local"])

    assert "✗ Local configuration needs a Git repository" in flat(result.output)
    assert "use --global" in flat(result.output)


@pytest.mark.usefixtures("outside_repository")
def test_resolved_view_lists_only_built_in_defaults_when_nothing_is_configured() -> None:
    result = runner.invoke(app, ["config", "list"])

    assert result.exit_code == 0, result.output
    assert "Sources (later entries override earlier ones):" in result.output
    assert "defaults" in result.output
    assert "global" not in result.output
    assert "local" not in result.output


def test_resolved_view_lists_every_source_in_override_order(
    isolated_env, git_repo, monkeypatch
) -> None:
    isolated_env.config_dir.mkdir(parents=True, exist_ok=True)
    (isolated_env.config_dir / "config.toml").write_text("[network]\ntimeout = 40\n")
    (git_repo / ".diffsage.toml").write_text("[network]\ntimeout = 50\n")
    monkeypatch.setenv("DIFFSAGE_TIMEOUT", "60")

    result = runner.invoke(app, ["config", "get", "timeout"])

    assert result.exit_code == 0, result.output
    output = flat(result.output)
    assert output.index("defaults") < output.index("global") < output.index("local")
    assert output.index("local") < output.index("environment DIFFSAGE_TIMEOUT")
    assert "60" in output


def test_resolved_view_shows_long_paths_in_full(git_repo, monkeypatch) -> None:
    monkeypatch.setenv("COLUMNS", "60")
    (git_repo / ".diffsage.toml").write_text("[network]\ntimeout = 50\n")

    result = runner.invoke(app, ["config", "list"])

    assert result.exit_code == 0, result.output
    assert "…" not in result.output
    assert str(git_repo / ".diffsage.toml").replace(" ", "") in result.output.replace(
        "\n", ""
    ).replace(" ", "")
