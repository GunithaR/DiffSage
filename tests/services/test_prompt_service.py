from datetime import datetime

from diffsage.models.git import CommitContext, GitCommit, PullRequestContext
from diffsage.models.pull_request_analysis import (
    ChangeCategory,
    PullRequestAnalysis,
    RiskLevel,
)
from diffsage.services.prompt_service import PromptService


def test_build_commit_prompt() -> None:
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


def test_build_pull_request_prompt() -> None:
    context = PullRequestContext(
        current_branch="feature/pr-generation",
        base_branch="main",
        merge_base="merge1234",
        commits=[
            GitCommit(
                hash="def5678",
                author="Test User",
                message="Add pull request generation",
                date=datetime(2026, 8, 16, 12, 0, 0),
            ),
            GitCommit(
                hash="ghi9012",
                author="Test User",
                message="Add PR analysis",
                date=datetime(2026, 8, 16, 13, 0, 0),
            ),
        ],
        changed_files=[
            "src/services/pull_request_service.py",
            "tests/services/test_pull_request_service.py",
        ],
        diff="""diff --git a/src/services/pull_request_service.py
+class PullRequestService:
+    pass
""",
    )

    analysis = PullRequestAnalysis(
        changed_areas=[
            "services",
            "tests",
        ],
        change_categories=[
            ChangeCategory.TEST,
        ],
        risk_signals=[],
        risk_level=RiskLevel.LOW,
        reviewer_focus=[
            "test coverage and test changes",
        ],
    )

    service = PromptService()
    prompt = service.build_pull_request_prompt(context, analysis)

    assert context.current_branch in prompt
    assert context.base_branch in prompt
    assert context.merge_base in prompt

    for commit in context.commits:
        assert commit.hash in prompt
        assert commit.author in prompt
        assert commit.message in prompt
        assert str(commit.date) in prompt

    for changed_file in context.changed_files:
        assert changed_file in prompt

    assert context.diff in prompt

    for area in analysis.changed_areas:
        assert area in prompt

    for category in analysis.change_categories:
        assert category.value in prompt

    assert analysis.risk_level.value in prompt

    for signal in analysis.risk_signals:
        assert signal in prompt

    assert "Testing Evidence:" in prompt
    assert (
        "No repository tests, linters, audits, quality checks were executed by DiffSage." in prompt
    )

    for focus in analysis.reviewer_focus:
        assert focus in prompt


def test_build_pull_request_prompt_handles_empty_analysis_sections() -> None:
    context = PullRequestContext(
        current_branch="feature/example",
        base_branch="main",
        merge_base="abc123",
        commits=[],
        changed_files=["README.md"],
        diff="diff --git a/README.md b/README.md",
    )

    analysis = PullRequestAnalysis(
        risk_level=RiskLevel.LOW,
    )

    service = PromptService()

    prompt = service.build_pull_request_prompt(
        context,
        analysis,
    )

    assert context.current_branch in prompt
    assert context.base_branch in prompt
    assert context.merge_base in prompt
    assert context.changed_files[0] in prompt
    assert context.diff in prompt
    assert analysis.risk_level.value in prompt


def test_build_pull_request_prompt_includes_risk_signals() -> None:
    context = PullRequestContext(
        current_branch="feature/security",
        base_branch="main",
        merge_base="abc123",
        commits=[],
        changed_files=[
            "src/security/auth.py",
        ],
        diff="security-related diff",
    )

    analysis = PullRequestAnalysis(
        change_categories=[ChangeCategory.AUTHENTICATION],
        risk_signals=[
            "authentication/security-related paths changed",
        ],
        risk_level=RiskLevel.HIGH,
        reviewer_focus=[
            "authentication and security-related changes",
        ],
    )

    service = PromptService()

    prompt = service.build_pull_request_prompt(
        context,
        analysis,
    )

    assert "authentication/security-related paths changed" in prompt
    assert "high" in prompt
    assert "authentication and security-related changes" in prompt


def test_diff_notes_are_appended_and_tell_the_ai_to_ignore_placeholders() -> None:
    service = PromptService()
    context = CommitContext(branch="main", staged_diff="diff", unstaged_diff="", recent_commits=[])

    prompt = service.build_commit_prompt(context, ["Lockfile contents were not sent: uv.lock"])

    assert prompt.endswith(
        "Diff Notes:\n"
        "DiffSage removed or redacted some content before sending this diff. Treat the "
        "placeholders as unchanged details, never as changes, and do not mention them.\n"
        "- Lockfile contents were not sent: uv.lock"
    )


def test_prompt_without_notes_has_no_notes_section() -> None:
    service = PromptService()
    context = CommitContext(branch="main", staged_diff="diff", unstaged_diff="", recent_commits=[])

    assert "Diff Notes" not in service.build_commit_prompt(context)
    assert "Diff Notes" not in service.build_commit_prompt(context, [])
