import subprocess
from pathlib import Path

import pytest

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
from diffsage.models.pull_request import PullRequestDraft
from diffsage.services.ai_service import AIService
from diffsage.services.credentials_service import CredentialService
from diffsage.services.github_service import GitHubService
from diffsage.storage.credentials_repository import CredentialsRepository


def create_ai_service() -> AIService:
    repository = CredentialsRepository(get_credentials_path())
    return AIService(load_settings(), CredentialService(repository))


def create_draft() -> PullRequestDraft:
    return PullRequestDraft(title="Add feature", summary="Adds a feature.", why="Needed.")


def test_isolated_env_redirects_config_credentials_and_logs(isolated_env) -> None:
    assert get_global_config_path().is_relative_to(isolated_env.config_dir)
    assert get_credentials_path().is_relative_to(isolated_env.config_dir)
    assert get_log_file_path().is_relative_to(isolated_env.log_dir)


def test_isolated_env_ignores_diffsage_environment_variables(isolated_env) -> None:
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
    monkeypatch.setattr("diffsage.services.ai_service.time.sleep", lambda seconds: None)
    fake_provider.queue(ProviderUnavailableError("down"), "recovered")

    response = create_ai_service().ask("prompt")

    assert response.content == "recovered"
    assert len(fake_provider.requests) == 2


def test_fake_provider_fails_loudly_without_queued_response(fake_provider) -> None:
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


def test_git_remote_tracks_main(git_repo: Path, git_remote: Path) -> None:
    client = GitClient()

    assert client.remote_branch_commit("main") == client.current_commit()
    assert client.default_branch() == "main"
