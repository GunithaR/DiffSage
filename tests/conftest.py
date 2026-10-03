from dataclasses import dataclass
from pathlib import Path

import pytest

from diffsage.config.paths import get_credentials_path
from diffsage.github.client import GitHubClient
from diffsage.models.credentials import Credential
from diffsage.storage.credentials_repository import CredentialsRepository
from tests.fakes import FakeGitHubCLI, FakeProvider
from tests.helpers import init_git_repo_with_initial_commit, run_git


@pytest.fixture
def clean_diffsage_env(monkeypatch):
    variables = [
        "DIFFSAGE_PROVIDER",
        "DIFFSAGE_AI_MODEL",
        "DIFFSAGE_TIMEOUT",
        "DIFFSAGE_MAX_RETRIES",
        "DIFFSAGE_LOG_LEVEL",
    ]

    for variable in variables:
        monkeypatch.delenv(variable, raising=False)


@dataclass(slots=True)
class IsolatedEnv:
    config_dir: Path
    log_dir: Path


@pytest.fixture
def isolated_env(tmp_path, monkeypatch, clean_diffsage_env) -> IsolatedEnv:
    """Keep DiffSage away from the developer's real config, credentials, logs and .env.

    platformdirs is patched directly because on Windows it ignores HOME-style
    environment variables.
    """

    config_dir = tmp_path / "config"
    log_dir = tmp_path / "logs"

    monkeypatch.setattr(
        "diffsage.config.paths.user_config_path",
        lambda *args, **kwargs: config_dir,
    )
    monkeypatch.setattr(
        "diffsage.config.paths.user_log_path",
        lambda *args, **kwargs: log_dir,
    )
    monkeypatch.setattr(
        "diffsage.config.resolver.load_dotenv",
        lambda *args, **kwargs: False,
    )
    monkeypatch.setattr("diffsage.logging.logger._CONFIGURED", True)

    return IsolatedEnv(config_dir=config_dir, log_dir=log_dir)


@pytest.fixture
def git_repo(tmp_path, monkeypatch) -> Path:
    """A Git repository with one commit on main, used as the working directory."""

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

    stored = Credential(provider="gemini", name="default", api_key="test-api-key")
    CredentialsRepository(get_credentials_path()).save(stored)

    return stored


@pytest.fixture
def fake_provider(monkeypatch, credential) -> FakeProvider:
    """Replace the real AI provider with a FakeProvider for every AIService."""

    provider = FakeProvider()

    monkeypatch.setattr(
        "diffsage.services.ai_service.create_provider",
        lambda settings, credential: provider,
    )

    return provider


@pytest.fixture
def fake_gh(tmp_path, monkeypatch) -> FakeGitHubCLI:
    """Route GitHubClient through the fake GitHub CLI."""

    cli = FakeGitHubCLI(tmp_path / "fake_gh_state.json")

    monkeypatch.setattr(
        GitHubClient,
        "_run_gh_command",
        lambda self, args: cli.run(args),
    )

    return cli
