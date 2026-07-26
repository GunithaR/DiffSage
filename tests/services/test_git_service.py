from pathlib import Path

from diffsage.services.git_service import GitService
from diffsage.git.client import GitClient
from diffsage.models.git import CommitContext

from tests.helpers import init_git_repo_with_initial_commit


def test_build_commit_context_returns_commit_context(tmp_path: Path):
    init_git_repo_with_initial_commit(tmp_path)

    readme = tmp_path / "README.md"
    readme.write_text("# DiffSage\n\nHello!")

    client = GitClient(tmp_path)
    service = GitService(client)

    context = service.build_commit_context()

    print(context)

    print(context.branch)

    assert isinstance(context, CommitContext)

    assert context.branch == "main"
    assert context.staged_diff == ""
    assert "Hello!" in context.unstaged_diff

    assert len(context.recent_commits) == 1
    assert context.recent_commits[0].message == "Initial Commit"
