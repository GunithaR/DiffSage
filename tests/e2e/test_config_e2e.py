"""End-to-end tests for `diffsage config`: real CLI, isolated config files."""

import os
import subprocess
import sys
from pathlib import Path

import pytest
from typer.testing import CliRunner

from diffsage.cli import app
from diffsage.config.paths import display_path, get_local_config_path
from tests.helpers import init_git_repo_with_initial_commit, run_git

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

    # Expect exactly what DiffSage prints: its own path, home-shortened on every OS
    # (on Windows the temp folder is inside the home folder, so it starts with "~").
    shown = display_path(get_local_config_path())
    assert shown.replace(" ", "") in result.output.replace("\n", "").replace(" ", "")


def test_local_config_is_read_inside_git_worktree(git_repo, tmp_path, monkeypatch) -> None:
    """Regression: in a worktree .git is a file, so the repo root was not found."""

    worktree = tmp_path / "worktree"
    run_git(["worktree", "add", "-b", "feature/worktree", str(worktree)], git_repo)
    (worktree / ".diffsage.toml").write_text('[ai]\nmodel = "worktree-model"\n')
    monkeypatch.chdir(worktree)

    result = runner.invoke(app, ["config", "get", "model"])

    assert result.exit_code == 0, result.output
    assert "worktree-model" in result.output


def test_local_config_inside_submodule_is_the_submodules_own(
    git_repo, tmp_path, monkeypatch
) -> None:
    """Regression: in a submodule .git is a file, so the PARENT repo's config was used."""

    library = tmp_path / "library"
    library.mkdir()
    init_git_repo_with_initial_commit(library)
    run_git(
        ["-c", "protocol.file.allow=always", "submodule", "add", str(library), "libs/library"],
        git_repo,
    )
    (git_repo / ".diffsage.toml").write_text('[ai]\nmodel = "parent-model"\n')
    submodule = git_repo / "libs" / "library"
    (submodule / ".diffsage.toml").write_text('[ai]\nmodel = "submodule-model"\n')
    monkeypatch.chdir(submodule)

    result = runner.invoke(app, ["config", "get", "model"])

    assert result.exit_code == 0, result.output
    assert "submodule-model" in result.output
    assert "parent-model" not in result.output


def test_local_config_is_found_from_a_subdirectory(git_repo, monkeypatch) -> None:
    (git_repo / ".diffsage.toml").write_text('[ai]\nmodel = "root-model"\n')
    nested = git_repo / "src" / "package"
    nested.mkdir(parents=True)
    monkeypatch.chdir(nested)

    result = runner.invoke(app, ["config", "get", "model"])

    assert result.exit_code == 0, result.output
    assert "root-model" in result.output


def test_dotenv_files_are_not_loaded(git_repo, monkeypatch) -> None:
    """A .env file must never change settings or leak into DiffSage's environment."""

    (git_repo / ".env").write_text("DIFFSAGE_TIMEOUT=99\nUNRELATED_SECRET=hunter2\n")
    monkeypatch.delenv("UNRELATED_SECRET", raising=False)

    result = runner.invoke(app, ["config", "get", "timeout"])

    assert result.exit_code == 0, result.output
    assert "30" in result.output
    assert "99" not in result.output
    assert "environment" not in result.output
    assert "UNRELATED_SECRET" not in os.environ


def test_diffsage_does_not_import_dotenv() -> None:
    """Guards against .env loading coming back in any form, including a bare
    load_dotenv() that searches from DiffSage's install folder rather than the project."""

    code = "import sys, diffsage.cli; print('dotenv' in sys.modules)"
    result = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True, check=True
    )

    assert result.stdout.strip() == "False"


@pytest.mark.parametrize(
    ("args", "expected"),
    [
        (["timeout", "--", "-5"], "Invalid value '-5' for timeout: Input should be greater than"),
        (["max_retries", "999"], "Invalid value '999' for max_retries: Input should be less than"),
        (["log_level", "LOUD"], "Invalid value 'LOUD' for log_level: Input should be 'DEBUG'"),
        (["provider", "openai"], "Invalid value 'openai' for provider: Input should be 'gemini'"),
        (
            ["max_output_tokens", "0"],
            "Invalid value '0' for max_output_tokens: Input should be greater than or equal to 1",
        ),
        (
            ["max_output_tokens", "70000"],
            "Invalid value '70000' for max_output_tokens: Input should be less than or equal to "
            "65536",
        ),
    ],
)
def test_config_set_rejects_invalid_values_and_writes_nothing(isolated_env, args, expected) -> None:
    # --global goes first: a negative number needs "--", which ends option parsing.
    result = runner.invoke(app, ["config", "set", "--global", *args])

    assert result.exit_code == 1
    assert f"✗ {expected}" in flat(result.output)
    assert not (isolated_env.config_dir / "config.toml").exists()


def test_misspelled_keys_in_config_file_are_reported(isolated_env) -> None:
    isolated_env.config_dir.mkdir(parents=True, exist_ok=True)
    (isolated_env.config_dir / "config.toml").write_text(
        '[ai]\nmodle = "typo"\n\n[netwrok]\ntimeout = 5\n'
    )

    result = runner.invoke(app, ["config", "get", "model"])

    assert result.exit_code == 1
    assert "ai.modle: Extra inputs are not permitted" in flat(result.output)
    assert "netwrok: Extra inputs are not permitted" in flat(result.output)


def test_invalid_environment_variable_is_named(monkeypatch) -> None:
    monkeypatch.setenv("DIFFSAGE_TIMEOUT", "0")

    result = runner.invoke(app, ["config", "get", "timeout"])

    assert result.exit_code == 1
    assert (
        "✗ Invalid environment variable DIFFSAGE_TIMEOUT: Input should be greater than or "
        "equal to 1 (got '0')" in flat(result.output)
    )


def test_environment_and_file_values_are_normalised(isolated_env, monkeypatch) -> None:
    isolated_env.config_dir.mkdir(parents=True, exist_ok=True)
    (isolated_env.config_dir / "config.toml").write_text('[ai]\nprovider = "Gemini"\n')
    monkeypatch.setenv("DIFFSAGE_LOG_LEVEL", "debug")

    provider = runner.invoke(app, ["config", "get", "provider"])
    log_level = runner.invoke(app, ["config", "get", "log_level"])

    assert provider.exit_code == 0, provider.output
    assert "gemini" in provider.output
    assert log_level.exit_code == 0, log_level.output
    assert "DEBUG" in log_level.output


def test_config_set_keeps_model_case(isolated_env) -> None:
    result = runner.invoke(app, ["config", "set", "model", "Gemini-2.5-PRO", "--global"])

    assert result.exit_code == 0, result.output
    assert 'model = "Gemini-2.5-PRO"' in (isolated_env.config_dir / "config.toml").read_text()


@pytest.mark.parametrize(
    ("command", "expected"),
    [
        ("set", ["Write to the repository's .diffsage.toml.", "Write to your user-wide config"]),
        (
            "unset",
            ["Remove from the repository's .diffsage.toml.", "Remove from your user-wide config"],
        ),
        ("list", ["Read the repository's .diffsage.toml directly", "Read your user-wide config"]),
        ("get", ["Read the repository's .diffsage.toml directly", "Read your user-wide config"]),
    ],
)
def test_scope_option_help_describes_each_file(command, expected) -> None:
    """Regression: --global said "repository's global configuration", unset said "Write
    to", and list/get had no help for --local/--global."""

    result = runner.invoke(app, ["config", command, "--help"])

    assert result.exit_code == 0, result.output
    for text in expected:
        assert text in flat(result.output)
    assert "repository's global" not in result.output


def test_max_output_tokens_is_stored_in_the_ai_section_and_listed(isolated_env) -> None:
    result = runner.invoke(app, ["config", "set", "max_output_tokens", "4000", "--global"])

    assert result.exit_code == 0, result.output
    assert "[ai]\nmax_output_tokens = 4000" in (isolated_env.config_dir / "config.toml").read_text()

    listed = runner.invoke(app, ["config", "list"])

    assert "Max Output Tokens 4000" in flat(listed.output)
