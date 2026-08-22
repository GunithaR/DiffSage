import subprocess
from pathlib import Path
from unittest.mock import patch

from diffsage.github.client import GitHubClient


def test_is_available_returns_true_when_gh_is_installed(
    tmp_path: Path,
) -> None:
    client = GitHubClient(tmp_path)

    with patch(
        "diffsage.github.client.subprocess.run",
    ) as mock_run:
        assert client.is_available() is True

        mock_run.assert_called_once_with(
            ["gh", "--version"],
            cwd=tmp_path,
            capture_output=True,
            text=True,
            check=True,
        )


def test_is_available_returns_false_when_gh_is_not_installed(
    tmp_path: Path,
) -> None:
    client = GitHubClient(tmp_path)

    with patch(
        "diffsage.github.client.subprocess.run",
        side_effect=FileNotFoundError,
    ):
        assert client.is_available() is False


def test_is_authenticated_returns_true_when_authenticated(
    tmp_path: Path,
) -> None:
    client = GitHubClient(tmp_path)

    with patch(
        "diffsage.github.client.subprocess.run",
    ) as mock_run:
        assert client.is_authenticated() is True

        mock_run.assert_called_once_with(
            ["gh", "auth", "status"],
            cwd=tmp_path,
            capture_output=True,
            text=True,
            check=True,
        )


def test_is_authenticated_returns_false_when_not_authenticated(
    tmp_path: Path,
) -> None:
    client = GitHubClient(tmp_path)

    with patch(
        "diffsage.github.client.subprocess.run",
        side_effect=subprocess.CalledProcessError(
            returncode=1,
            cmd=["gh", "auth", "status"],
        ),
    ):
        assert client.is_authenticated() is False


def test_create_pull_request_returns_pull_request_url(
    tmp_path: Path,
) -> None:
    client = GitHubClient(tmp_path)

    with patch(
        "diffsage.github.client.subprocess.run",
    ) as mock_run:
        mock_run.return_value.stdout = "https://github.com/example/repo/pull/42\n"

        result = client.create_pull_request(
            title="Add pull request generation",
            body="Adds generated pull request support.",
            base_branch="main",
            head_branch="feature/pr-generation",
        )

        assert result == "https://github.com/example/repo/pull/42"

        mock_run.assert_called_once_with(
            [
                "gh",
                "pr",
                "create",
                "--base",
                "main",
                "--head",
                "feature/pr-generation",
                "--title",
                "Add pull request generation",
                "--body",
                "Adds generated pull request support.",
            ],
            cwd=tmp_path,
            capture_output=True,
            text=True,
            check=True,
        )
