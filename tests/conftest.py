from dataclasses import dataclass
from pathlib import Path

import pytest

from diffsage.config.paths import get_credentials_path
from diffsage.github.client import GitHubClient
from diffsage.models.credentials import Credential
from diffsage.storage.credentials_repository import CredentialsRepository
from tests.fakes import FakeGitHubCLI, FakeProvider
from tests.helpers import init_git_repo_with_initial_commit, run_git

DIFFSAGE_ENV_VARIABLES = [
    "DIFFSAGE_PROVIDER",
    "DIFFSAGE_AI_MODEL",
    "DIFFSAGE_TIMEOUT",
    "DIFFSAGE_MAX_RETRIES",
    "DIFFSAGE_LOG_LEVEL",
]


def remove_diffsage_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for variable in DIFFSAGE_ENV_VARIABLES:
        monkeypatch.delenv(variable, raising=False)


@pytest.fixture
def clean_diffsage_env(monkeypatch):
    remove_diffsage_env(monkeypatch)


@dataclass(slots=True)
class IsolatedEnv:
    config_dir: Path
    log_dir: Path


@pytest.fixture
def isolated_env(tmp_path, monkeypatch) -> IsolatedEnv:
    """Keep DiffSage away from the developer's real config, credentials, logs and .env.

    platformdirs is patched directly because on Windows it ignores HOME-style
    environment variables.
    """

    remove_diffsage_env(monkeypatch)

    config_dir = tmp_path / "config"
    log_dir = tmp_path / "logs"

    monkeypatch.setattr(
        "diffsage.config.paths.user_config_path",
        lambda *_args, **_kwargs: config_dir,
    )
    monkeypatch.setattr(
        "diffsage.config.paths.user_log_path",
        lambda *_args, **_kwargs: log_dir,
    )
    monkeypatch.setattr(
        "diffsage.config.resolver.load_dotenv",
        lambda *_args, **_kwargs: False,
    )
    monkeypatch.setattr("diffsage.logging.logger._CONFIGURED", True)

    # Rich wraps at the terminal width; a wide fixed width keeps asserted
    # messages on one line on every CI runner.
    monkeypatch.setenv("COLUMNS", "200")

    return IsolatedEnv(config_dir=config_dir, log_dir=log_dir)


@pytest.fixture
def git_repo(tmp_path, monkeypatch) -> Path:
    """A Git repository with one commit on main, used as the working directory.

    The developer's global and system Git config (signing, hooks, aliases) is
    hidden so commits made by DiffSage behave the same on every machine.
    """

    global_config = tmp_path / "gitconfig"
    global_config.touch()
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(global_config))
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")

    repo = tmp_path / "repo"
    repo.mkdir()
    init_git_repo_with_initial_commit(repo)

    monkeypatch.chdir(repo)

    return repo


@pytest.fixture
def git_remote(tmp_path, git_repo) -> Path:
    """A bare origin remote for git_repo, with main pushed and set as origin/HEAD."""

    remote = tmp_path / "remote.git"
    remote.mkdir()

    run_git(["init", "--bare", "--initial-branch=main"], remote)
    run_git(["remote", "add", "origin", str(remote)], git_repo)
    run_git(["push", "-u", "origin", "main"], git_repo)
    run_git(["remote", "set-head", "origin", "main"], git_repo)

    return remote


@pytest.fixture
def credential(isolated_env) -> Credential:
    """A stored default Gemini credential in the isolated config directory."""

    path = get_credentials_path()

    # Guard: never write a test credential over the developer's real one.
    assert path.is_relative_to(isolated_env.config_dir)

    stored = Credential(provider="gemini", name="default", api_key="test-api-key")
    CredentialsRepository(path).save(stored)

    return stored


@pytest.fixture
def fake_provider(monkeypatch, credential) -> FakeProvider:
    """Replace the real AI provider with a FakeProvider for every AIService."""

    provider = FakeProvider()

    def create_fake_provider(_settings, used_credential: Credential) -> FakeProvider:
        assert used_credential == credential
        return provider

    monkeypatch.setattr(
        "diffsage.services.ai_service.create_provider",
        create_fake_provider,
    )

    return provider


@pytest.fixture
def fake_gh(tmp_path, monkeypatch) -> FakeGitHubCLI:
    """Route GitHubClient through the fake GitHub CLI."""

    cli = FakeGitHubCLI(tmp_path / "fake_gh_state.json")

    monkeypatch.setattr(
        GitHubClient,
        "_run_gh_command",
        lambda _self, args: cli.run(args),
    )

    return cli
