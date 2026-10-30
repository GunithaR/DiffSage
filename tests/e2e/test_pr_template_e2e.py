"""End-to-end tests for filling in the repository's own pull request template."""

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from diffsage.cli import app
from diffsage.git.client import GitClient
from diffsage.parsers.pull_request_parser import (
    PULL_REQUEST_DRAFT_SCHEMA,
    TEMPLATED_DRAFT_SCHEMA,
)
from diffsage.services.git_service import GitService
from tests.helpers import run_git

runner = CliRunner()

TEMPLATE = """## What does this change?
<!-- Describe the change. -->

## Ticket
<!-- JIRA-123 -->

- [ ] Tests added
- [ ] Docs updated
"""

FILLED = """## What does this change?
Adds a greeting script.

## Ticket
Not applicable.

- [ ] Tests added
- [ ] Docs updated"""

FIXED_DRAFT = json.dumps(
    {
        "title": "Add greeting script",
        "summary": "Adds a script.",
        "why": "Needed.",
        "changes": [],
        "testing": [],
        "risks": [],
        "reviewer_focus": [],
        "breaking_changes": [],
    }
)


def commit_file(repo: Path, path: str, content: str) -> None:
    (repo / path).parent.mkdir(parents=True, exist_ok=True)
    (repo / path).write_text(content)
    run_git(["add", path], repo)
    run_git(["commit", "-m", f"chore: add {path}"], repo)


def start_feature(repo: Path) -> None:
    run_git(["switch", "-c", "feature/greeting"], repo)
    commit_file(repo, "greeting.py", "print('hello')\n")
    run_git(["push", "-u", "origin", "feature/greeting"], repo)


@pytest.mark.usefixtures("git_remote")
def test_pr_fills_in_the_template_from_the_base_branch(git_repo, fake_provider, fake_gh) -> None:
    commit_file(git_repo, ".github/PULL_REQUEST_TEMPLATE.md", TEMPLATE)
    run_git(["push", "origin", "main"], git_repo)
    start_feature(git_repo)
    fake_provider.queue(json.dumps({"title": "Add greeting script", "body": FILLED}))

    result = runner.invoke(app, ["pr"], input="y\n")

    assert result.exit_code == 0, result.output
    assert (
        "Filling in the repository's pull request template (.github/PULL_REQUEST_TEMPLATE.md)."
        in result.output
    )
    request = fake_provider.requests[0]
    assert request.response_schema == TEMPLATED_DRAFT_SCHEMA
    assert f"Pull Request Template:\n{TEMPLATE.strip()}" in request.prompt
    assert "Not applicable." in result.output  # the filled body is shown for review
    assert fake_gh.bodies == [FILLED]


@pytest.mark.usefixtures("git_remote")
def test_template_only_on_the_feature_branch_is_not_used(git_repo, fake_provider, fake_gh) -> None:
    """GitHub takes the template from the base branch, so DiffSage does too."""

    start_feature(git_repo)
    commit_file(git_repo, ".github/pull_request_template.md", TEMPLATE)
    run_git(["push"], git_repo)
    fake_provider.queue(FIXED_DRAFT)

    result = runner.invoke(app, ["pr"], input="y\n")

    assert result.exit_code == 0, result.output
    assert fake_provider.requests[0].response_schema == PULL_REQUEST_DRAFT_SCHEMA
    assert "## Summary" in fake_gh.bodies[0]


@pytest.mark.parametrize(
    ("files", "expected"),
    [
        (
            {
                "docs/pull_request_template.md": "docs",
                "pull_request_template.md": "root",
                ".github/pull_request_template.md": "github",
            },
            (".github/pull_request_template.md", "github"),
        ),
        (
            {"docs/pull_request_template.md": "docs", "Pull_Request_Template.md": "root"},
            ("Pull_Request_Template.md", "root"),
        ),
        ({"docs/pull_request_template.md": "docs"}, ("docs/pull_request_template.md", "docs")),
        ({".github/pull_request_template.md": "  \n", "docs/pull_request_template.md": "docs"},
         ("docs/pull_request_template.md", "docs")),
        ({"docs/notes.md": "not a template"}, None),
    ],
    ids=["github-first", "root-any-case", "docs", "empty-skipped", "none"],
)  # fmt: skip
def test_template_is_found_where_github_looks_for_it(git_repo, files, expected) -> None:
    for path, content in files.items():
        commit_file(git_repo, path, content)

    assert GitService(GitClient(git_repo)).pull_request_template("HEAD") == expected
