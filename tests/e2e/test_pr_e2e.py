"""End-to-end tests for `diffsage pr`: real CLI, real Git repository with an origin
remote, fake AI provider and fake GitHub CLI."""

import json
import sys
from pathlib import Path

import pytest
from typer.testing import CliRunner

from diffsage.cli import app
from diffsage.commands.error_handler import UNEXPECTED_ERROR_MESSAGE
from diffsage.parsers.pull_request_parser import PULL_REQUEST_DRAFT_SCHEMA
from tests.helpers import run_git

runner = CliRunner()

DRAFT = {
    "title": "Add greeting script",
    "summary": "Adds a script that prints a greeting.",
    "why": "Gives new users a first command to run.",
    "changes": ["Add greeting.py."],
    "testing": ["Testing status was not provided."],
    "risks": [],
    "reviewer_focus": ["The greeting text."],
    "breaking_changes": [],
}


def draft_json(**changes: object) -> str:
    return json.dumps({**DRAFT, **changes})


def commit_file(repo: Path, name: str, content: str, message: str) -> None:
    (repo / name).write_text(content)
    run_git(["add", name], repo)
    run_git(["commit", "-m", message], repo)


@pytest.fixture
def feature_branch(git_repo: Path, git_remote: Path) -> Path:
    """A pushed feature branch with one commit ahead of main."""

    run_git(["switch", "-c", "feature/greeting"], git_repo)
    commit_file(git_repo, "greeting.py", "print('hello')\n", "feat: add greeting script")
    run_git(["push", "-u", "origin", "feature/greeting"], git_repo)

    assert run_git(["branch", "--list", "feature/greeting"], git_remote).stdout.strip()

    return git_repo


def pr_create_call(calls: list[list[str]]) -> list[str] | None:
    return next((call for call in calls if call[:2] == ["pr", "create"]), None)


@pytest.mark.usefixtures("feature_branch")
def test_pr_accept_creates_pull_request(fake_provider, fake_gh) -> None:
    fake_provider.queue(draft_json())

    result = runner.invoke(app, ["pr"], input="y\n")

    assert result.exit_code == 0, result.output
    assert "Pull request created successfully" in result.output
    assert "https://github.com/example/repo/pull/1" in result.output

    call = pr_create_call(fake_gh.calls)
    assert call is not None
    assert call[2:8] == [
        "--base",
        "main",
        "--head",
        "feature/greeting",
        "--title",
        "Add greeting script",
    ]
    assert call[8:10] == ["--body-file", "-"]
    assert "## Summary\nAdds a script that prints a greeting." in fake_gh.bodies[0]


@pytest.mark.usefixtures("feature_branch", "fake_gh")
def test_pr_prompt_contains_branch_evidence(fake_provider) -> None:
    fake_provider.queue(draft_json())

    runner.invoke(app, ["pr"], input="n\n")

    prompt = fake_provider.prompts[0]
    assert "Current Branch:\nfeature/greeting" in prompt
    assert "Base Branch:\nmain" in prompt
    assert "greeting.py" in prompt
    assert "feat: add greeting script" in prompt


@pytest.mark.usefixtures("feature_branch", "fake_gh")
def test_pr_shows_resolved_branches(fake_provider) -> None:
    fake_provider.queue(draft_json())

    result = runner.invoke(app, ["pr"], input="n\n")

    assert "Head: feature/greeting" in result.output
    assert "Base: main" in result.output


@pytest.mark.usefixtures("feature_branch")
def test_pr_cancel_creates_nothing(fake_provider, fake_gh) -> None:
    fake_provider.queue(draft_json())

    result = runner.invoke(app, ["pr"], input="n\n")

    assert result.exit_code == 0, result.output
    assert "Cancelled" in result.output
    assert pr_create_call(fake_gh.calls) is None


@pytest.mark.usefixtures("feature_branch")
def test_pr_regenerate_uses_second_draft(fake_provider, fake_gh) -> None:
    fake_provider.queue(draft_json(title="First draft"), draft_json(title="Second draft"))

    result = runner.invoke(app, ["pr"], input="r\ny\n")

    assert result.exit_code == 0, result.output
    assert len(fake_provider.prompts) == 2
    assert pr_create_call(fake_gh.calls)[7] == "Second draft"


def test_pr_against_explicit_base_branch(feature_branch, fake_provider, fake_gh) -> None:
    run_git(["branch", "develop", "main"], feature_branch)
    run_git(["push", "origin", "develop"], feature_branch)
    fake_provider.queue(draft_json())

    result = runner.invoke(app, ["pr", "develop"], input="y\n")

    assert result.exit_code == 0, result.output
    assert pr_create_call(fake_gh.calls)[2:4] == ["--base", "develop"]


@pytest.mark.usefixtures("fake_gh")
def test_pr_with_unpushed_commits_exits_before_ai(feature_branch, fake_provider) -> None:
    commit_file(feature_branch, "extra.py", "print('extra')\n", "feat: add extra script")

    result = runner.invoke(app, ["pr"])

    assert result.exit_code == 1
    assert "commits that have not been pushed" in result.output
    assert fake_provider.requests == []


@pytest.mark.usefixtures("git_remote", "fake_provider", "fake_gh")
def test_pr_with_unpushed_branch_exits(git_repo) -> None:
    run_git(["switch", "-c", "feature/local-only"], git_repo)
    commit_file(git_repo, "local.py", "print('local')\n", "feat: add local script")

    result = runner.invoke(app, ["pr"])

    assert result.exit_code == 1
    assert (
        "✗ Branch 'feature/local-only' does not exist on origin. Push it first: "
        "git push -u origin feature/local-only" in " ".join(result.output.split())
    )


@pytest.mark.usefixtures("git_remote", "fake_provider", "fake_gh")
def test_pr_on_base_branch_exits() -> None:
    result = runner.invoke(app, ["pr"])

    assert result.exit_code == 1
    assert (
        "✗ 'main' is both the current branch and the base branch. Switch to the branch you "
        "want to open a pull request for" in " ".join(result.output.split())
    )


@pytest.mark.usefixtures("feature_branch")
def test_pr_unauthenticated_gh_exits_before_ai(fake_provider, fake_gh) -> None:
    fake_gh.configure(authenticated=False)

    result = runner.invoke(app, ["pr"])

    assert result.exit_code == 1
    assert "gh auth login" in result.output
    assert fake_provider.requests == []


@pytest.mark.usefixtures("feature_branch", "fake_provider")
def test_pr_without_gh_installed_exits(fake_gh) -> None:
    fake_gh.installed = False

    result = runner.invoke(app, ["pr"])

    assert result.exit_code == 1
    assert "GitHub CLI is not installed" in result.output


@pytest.mark.usefixtures("feature_branch")
def test_pr_invalid_ai_json_exits(fake_provider, fake_gh) -> None:
    fake_provider.queue("This is not JSON")

    result = runner.invoke(app, ["pr"])

    assert result.exit_code == 1
    assert "The pull request draft is not valid JSON." in result.output
    assert pr_create_call(fake_gh.calls) is None


@pytest.mark.usefixtures("feature_branch")
def test_pr_reports_gh_create_failure_with_gh_message(fake_provider, fake_gh) -> None:
    """Regression: a failing `gh pr create` was reported as an unexpected error."""

    fake_gh.configure(
        pr_create_error='a pull request for branch "feature/greeting" into branch "main" '
        "already exists:\nhttps://github.com/example/repo/pull/7"
    )
    fake_provider.queue(draft_json())

    result = runner.invoke(app, ["pr"], input="y\n")

    assert result.exit_code == 1
    assert (
        '✗ GitHub CLI could not create the pull request: a pull request for branch "feature/'
        'greeting" into branch "main" already exists:' in result.output
    )
    assert "https://github.com/example/repo/pull/7" in result.output
    assert UNEXPECTED_ERROR_MESSAGE not in result.output


@pytest.mark.usefixtures("git_remote")
def test_pr_never_sends_secrets_to_the_ai(git_repo, fake_provider, fake_gh) -> None:
    secret = "ghp_" + "a" * 36
    run_git(["switch", "-c", "feature/secret"], git_repo)
    commit_file(
        git_repo, "deploy.sh", f"export GITHUB_TOKEN={secret}\n", "chore: add deploy script"
    )
    run_git(["push", "-u", "origin", "feature/secret"], git_repo)
    fake_provider.queue(draft_json())

    result = runner.invoke(app, ["pr"], input="n\n")

    assert result.exit_code == 0, result.output
    assert secret not in fake_provider.prompts[0]
    assert "[REDACTED]" in fake_provider.prompts[0]
    assert "! 1 value(s) that looked like secrets were replaced" in result.output
    assert pr_create_call(fake_gh.calls) is None


@pytest.mark.usefixtures("feature_branch")
def test_cancelled_pr_edit_keeps_the_draft(fake_provider, fake_gh, monkeypatch) -> None:
    python = sys.executable.replace("\\", "/")
    monkeypatch.setenv("GIT_EDITOR", f'"{python}" -c "import sys; sys.exit(1)"')
    fake_provider.queue(draft_json())

    result = runner.invoke(app, ["pr"], input="e\ny\n")

    assert result.exit_code == 0, result.output
    assert "! Edit cancelled. The draft is unchanged." in result.output
    assert pr_create_call(fake_gh.calls)[7] == "Add greeting script"


@pytest.mark.usefixtures("feature_branch", "fake_gh")
def test_pr_asks_the_ai_for_a_reply_in_the_draft_schema(fake_provider) -> None:
    fake_provider.queue(draft_json())

    runner.invoke(app, ["pr"], input="n\n")

    assert fake_provider.requests[0].response_schema == PULL_REQUEST_DRAFT_SCHEMA


@pytest.mark.usefixtures("feature_branch")
def test_pr_accepts_a_draft_wrapped_in_a_code_fence(fake_provider, fake_gh) -> None:
    fake_provider.queue(f"Here is the draft:\n```json\n{draft_json()}\n```")

    result = runner.invoke(app, ["pr"], input="y\n")

    assert result.exit_code == 0, result.output
    assert "Pull request created successfully" in result.output
    assert pr_create_call(fake_gh.calls) is not None


@pytest.mark.usefixtures("feature_branch")
def test_pr_stops_before_the_ai_when_a_pull_request_is_already_open(fake_provider, fake_gh) -> None:
    """Regression: the AI drafted a whole PR, and only `gh pr create` at the end failed
    with "a pull request already exists"."""

    url = "https://github.com/example/repo/pull/9"
    fake_gh.configure(open_prs=[{"url": url, "head": "feature/greeting", "base": "main"}])

    result = runner.invoke(app, ["pr"])

    assert result.exit_code == 1
    assert (
        f"✗ A pull request from 'feature/greeting' into 'main' is already open: {url}"
        in " ".join(result.output.split())
    )
    assert fake_provider.requests == []
    assert pr_create_call(fake_gh.calls) is None


@pytest.mark.usefixtures("feature_branch")
def test_pr_into_another_base_is_not_blocked_by_an_open_pr(fake_provider, fake_gh) -> None:
    fake_gh.configure(
        open_prs=[{"url": "https://example/pull/9", "head": "feature/greeting", "base": "dev"}]
    )
    fake_provider.queue(draft_json())

    result = runner.invoke(app, ["pr"], input="y\n")

    assert result.exit_code == 0, result.output
    assert pr_create_call(fake_gh.calls) is not None


@pytest.mark.usefixtures("feature_branch")
def test_pr_continues_when_open_prs_cannot_be_listed(fake_provider, fake_gh) -> None:
    fake_gh.configure(pr_list_error="HTTP 502: Bad Gateway")
    fake_provider.queue(draft_json())

    result = runner.invoke(app, ["pr"], input="y\n")

    assert result.exit_code == 0, result.output
    assert pr_create_call(fake_gh.calls) is not None


@pytest.mark.usefixtures("feature_branch")
def test_pr_body_reaches_gh_intact_through_stdin(fake_provider, fake_gh) -> None:
    """Long and non-ASCII bodies go through stdin, not the command line, which is limited
    to 32,767 characters on Windows."""

    long_why = "Café ✓ — " + "x" * 40_000
    fake_provider.queue(draft_json(why=long_why))

    result = runner.invoke(app, ["pr"], input="y\n")

    assert result.exit_code == 0, result.output
    assert f"## Why\n{long_why}" in fake_gh.bodies[0]
    assert all(len(arg) < 1_000 for arg in pr_create_call(fake_gh.calls))


@pytest.mark.usefixtures("feature_branch", "fake_gh")
def test_invalid_pr_edit_names_the_bad_fields_without_blaming_the_ai(
    fake_provider, monkeypatch, tmp_path
) -> None:
    """Regression: a hand edit with a missing field was reported as "AI response contains
    invalid or missing pull request fields", without saying which."""

    script = tmp_path / "break_draft.py"
    script.write_text(
        "import json, sys\n"
        "path = sys.argv[1]\n"
        "draft = json.load(open(path, encoding='utf-8'))\n"
        "del draft['why']\n"
        "draft['notes'] = 'extra'\n"
        "json.dump(draft, open(path, 'w', encoding='utf-8'))\n"
    )
    python = sys.executable.replace("\\", "/")
    monkeypatch.setenv("GIT_EDITOR", f'"{python}" "{script.as_posix()}"')
    fake_provider.queue(draft_json())

    result = runner.invoke(app, ["pr"], input="e\nn\n")

    assert result.exit_code == 0, result.output
    assert (
        "✗ The pull request draft has invalid fields: missing why; unexpected notes."
        in " ".join(result.output.split())
    )
    assert "AI response" not in result.output


@pytest.mark.usefixtures("git_remote", "fake_provider", "fake_gh")
def test_pr_on_detached_head_says_how_to_get_back_on_a_branch(git_repo) -> None:
    run_git(["switch", "--detach"], git_repo)

    result = runner.invoke(app, ["pr"])

    assert result.exit_code == 1
    assert (
        "✗ Cannot generate a pull request from a detached HEAD. Switch to a branch first: "
        "git switch <branch>" in " ".join(result.output.split())
    )


@pytest.mark.usefixtures("feature_branch")
def test_pr_does_not_spend_a_network_call_on_gh_auth_status(fake_provider, fake_gh) -> None:
    """The open-pull-request lookup already needs a login, so a separate `gh auth status`
    round trip is not made."""

    fake_provider.queue(draft_json())

    runner.invoke(app, ["pr"], input="n\n")

    assert ["auth", "status"] not in fake_gh.calls
    assert [call[:2] for call in fake_gh.calls] == [["--version"], ["pr", "list"]]


def test_pr_diff_limit_follows_the_environment(
    feature_branch, fake_provider, fake_gh, monkeypatch
) -> None:
    commit_file(feature_branch, "big.py", "# big\n" + "x = 1\n" * 400, "feat: add big file")
    run_git(["push"], feature_branch)
    monkeypatch.setenv("DIFFSAGE_MAX_DIFF_CHARACTERS", "1000")
    fake_provider.queue(draft_json())

    result = runner.invoke(app, ["pr"], input="n\n")

    assert result.exit_code == 0, result.output
    assert "x = 1\n" * 400 not in fake_provider.prompts[0]
    assert "diffsage config set max_diff_characters <characters>" in " ".join(result.output.split())
    assert fake_gh.calls
