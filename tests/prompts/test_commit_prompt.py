from datetime import datetime

from diffsage.models.git import CommitContext, GitCommit
from diffsage.services.prompt_service import PromptService


def make_context() -> CommitContext:
    return CommitContext(
        branch="test",
        staged_diff="""\
diff --git a/README.md b/README.md
+New Content
""",
        unstaged_diff="",
        recent_commits=[
            GitCommit(
                hash="1234567",
                author="Test User",
                message="Initial commit",
                date=datetime.now(),
            )
        ],
    )

def test_build_commit_prompt_includes_diff():
    service = PromptService()

    prompt = service.build_commit_prompt(make_context())

    assert "diff --git a/README.md b/README.md" in prompt
    assert "+New Content" in prompt

def test_build_commit_prompt_contains_commit_instructions():
    service = PromptService()

    prompt = service.build_commit_prompt(make_context())

    assert "Conventional Commit" in prompt
    assert "Return only the commit message" in prompt
    assert "If a body is included, it MUST contain 3–6 bullet points." in prompt