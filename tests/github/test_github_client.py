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
            input=None,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
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
            input=None,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
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
                "--body-file",
                "-",
            ],
            cwd=tmp_path,
            input="Adds generated pull request support.",
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=True,
        )


def gh_output(stdout: str):
    return subprocess.CompletedProcess(["gh"], 0, stdout=stdout, stderr="")


def test_open_pull_request_url_asks_gh_for_open_prs_of_the_branch_pair(tmp_path: Path) -> None:
    client = GitHubClient(tmp_path)
    url = "https://github.com/example/repo/pull/7"

    with patch(
        "diffsage.github.client.subprocess.run",
        return_value=gh_output(f'[{{"number": 7, "url": "{url}"}}]'),
    ) as mock_run:
        assert client.open_pull_request_url("feature/x", "main") == url

    assert mock_run.call_args.args[0] == [
        "gh", "pr", "list", "--head", "feature/x", "--base", "main",
        "--state", "open", "--json", "number,url", "--limit", "1",
    ]  # fmt: skip


def test_open_pull_request_url_is_none_without_an_open_pr(tmp_path: Path) -> None:
    with patch("diffsage.github.client.subprocess.run", return_value=gh_output("[]\n")):
        assert GitHubClient(tmp_path).open_pull_request_url("feature/x", "main") is None
