import socket
import subprocess
from pathlib import Path

import pytest
from typer.testing import CliRunner

from diffsage.cli import app
from diffsage.config.loader import load_settings
from diffsage.config.paths import (
    get_credentials_path,
    get_global_config_path,
    get_log_file_path,
)
from diffsage.exceptions import (
    GitHubAuthenticationError,
    GitHubCLIUnavailableError,
    ProviderUnavailableError,
)
from diffsage.git.client import GitClient
from diffsage.github.client import GitHubClient
from diffsage.models.credentials import Credential
from diffsage.models.pull_request import PullRequestDraft
from diffsage.providers.gemini_provider import GeminiProvider
from diffsage.services.ai_service import AIService
from diffsage.services.credentials_service import CredentialService
from diffsage.services.github_service import GitHubService
from diffsage.storage.credentials_repository import CredentialsRepository
from tests.helpers import create_settings
from tests.network_guard import RealServiceAccessError


def create_ai_service() -> AIService:
    repository = CredentialsRepository(get_credentials_path())
    return AIService(load_settings(), CredentialService(repository))


def create_draft() -> PullRequestDraft:
    return PullRequestDraft(title="Add feature", summary="Adds a feature.", why="Needed.")


def test_isolated_env_redirects_config_credentials_and_logs(isolated_env) -> None:
    assert get_global_config_path().is_relative_to(isolated_env.config_dir)
    assert get_credentials_path().is_relative_to(isolated_env.config_dir)
    assert get_log_file_path().is_relative_to(isolated_env.log_dir)


@pytest.mark.usefixtures("isolated_env")
def test_isolated_env_ignores_diffsage_environment_variables() -> None:
    settings = load_settings()

    assert settings.provider == "gemini"
    assert settings.max_retries == 3


def test_fake_provider_returns_queued_responses_and_records_prompts(fake_provider) -> None:
    fake_provider.queue("first", "second")
    service = create_ai_service()

    assert service.ask("prompt one").content == "first"
    assert service.ask("prompt two").content == "second"
    assert fake_provider.prompts == ["prompt one", "prompt two"]


def test_fake_provider_raises_queued_exceptions(fake_provider, monkeypatch) -> None:
    monkeypatch.setattr("diffsage.services.ai_service.time.sleep", lambda _seconds: None)
    fake_provider.queue(ProviderUnavailableError("down"), "recovered")

    response = create_ai_service().ask("prompt")

    assert response.content == "recovered"
    assert len(fake_provider.requests) == 2


@pytest.mark.usefixtures("fake_provider")
def test_fake_provider_fails_loudly_without_queued_response() -> None:
    with pytest.raises(AssertionError, match="no queued response"):
        create_ai_service().ask("prompt")


def test_fake_gh_validates_and_creates_pull_request(fake_gh) -> None:
    service = GitHubService(GitHubClient())

    service.validate()
    url = service.create_pull_request(create_draft(), base_branch="main", head_branch="feature")

    assert url == "https://github.com/example/repo/pull/1"
    assert fake_gh.calls[0] == ["--version"]
    assert fake_gh.calls[1] == ["auth", "status"]
    assert fake_gh.calls[2][:6] == ["pr", "create", "--base", "main", "--head", "feature"]


def test_fake_gh_reports_unauthenticated(fake_gh) -> None:
    fake_gh.configure(authenticated=False)

    with pytest.raises(GitHubAuthenticationError):
        GitHubService(GitHubClient()).validate()


def test_fake_gh_reports_not_installed(fake_gh) -> None:
    fake_gh.installed = False

    with pytest.raises(GitHubCLIUnavailableError):
        GitHubService(GitHubClient()).validate()


def test_fake_gh_pull_request_failure_carries_stderr(fake_gh) -> None:
    fake_gh.configure(pr_create_error="a pull request already exists")

    with pytest.raises(subprocess.CalledProcessError) as error:
        GitHubClient().create_pull_request("title", "body", "main", "feature")

    assert "a pull request already exists" in error.value.stderr


def test_git_repo_is_working_directory_with_one_commit(git_repo: Path) -> None:
    client = GitClient()

    assert Path.cwd() == git_repo
    assert client.is_git_repository()
    assert client.current_branch() == "main"
    assert len(client.recent_commits()) == 1


@pytest.mark.usefixtures("git_repo", "git_remote")
def test_git_remote_tracks_main() -> None:
    client = GitClient()

    assert client.remote_branch_commit("main") == client.current_commit()
    assert client.default_branch() == "main"


def test_isolated_env_ignores_local_config_where_pytest_started(isolated_env) -> None:
    assert Path.cwd() == isolated_env.workdir
    assert not (Path.cwd() / ".diffsage.toml").exists()


def test_creating_a_real_gemini_client_fails_the_test() -> None:
    with pytest.raises(RealServiceAccessError, match="real Gemini client"):
        GeminiProvider(create_settings(), Credential("gemini", "default", "dummy-key"))


@pytest.mark.usefixtures("credential")
def test_a_real_gemini_client_cannot_hide_behind_the_cli_error_handler() -> None:
    """The guard must not be reported as "unexpected error" and pass a test that
    expects the command to fail."""

    with pytest.raises(RealServiceAccessError):
        CliRunner().invoke(app, ["ask", "hello"], catch_exceptions=True)


@pytest.mark.parametrize(
    "connect",
    [
        lambda: socket.create_connection(("generativelanguage.googleapis.com", 443), timeout=1),
        lambda: socket.create_connection(("8.8.8.8", 53), timeout=1),
        lambda: socket.getaddrinfo("example.com", 80),
    ],
    ids=["by-name", "by-ip", "dns-lookup"],
)
def test_network_access_fails_the_test(connect) -> None:
    with pytest.raises(RealServiceAccessError):
        connect()


def test_local_sockets_still_work() -> None:
    with socket.create_server(("127.0.0.1", 0)) as server:
        port = server.getsockname()[1]

        with socket.create_connection(("127.0.0.1", port), timeout=1):
            pass

        with socket.create_connection(("localhost", port), timeout=1):
            pass
