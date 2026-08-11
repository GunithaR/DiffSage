from datetime import datetime

from diffsage.models.git import CommitContext, GitCommit
from diffsage.services.prompt_service import PromptService


def test_build_commit_prompt():
    commit_context = CommitContext(
        branch="main",
        staged_diff="""diff --git a/file.py b/file.py
        +print("Hello")
        """,
        unstaged_diff="""diff --git a/app.py b/app.py
        -def old()
        +def new()
        """,
        recent_commits=[
            GitCommit(
                hash="abc1234",
                author="Test User",
                message="Initial Commit",
                date=datetime(2026, 7, 23, 12, 8, 41, 588716),
            )
        ],
    )

    service = PromptService()
    prompt = service.build_commit_prompt(commit_context)

    assert commit_context.branch in prompt
    assert commit_context.staged_diff in prompt
    assert commit_context.unstaged_diff in prompt
    assert commit_context.recent_commits[0].message in prompt
