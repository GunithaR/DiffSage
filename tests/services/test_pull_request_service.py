from datetime import datetime
from unittest.mock import Mock

import pytest

from diffsage.exceptions import InvalidPullRequestDraftError
from diffsage.models.git import GitCommit, PullRequestContext
from diffsage.models.provider import ProviderResponse
from diffsage.models.pull_request import PullRequestDraft
from diffsage.models.pull_request_analysis import (
    PullRequestAnalysis,
    RiskLevel,
)
from diffsage.parsers.pull_request_parser import PullRequestParser
from diffsage.services.ai_service import AIService
from diffsage.services.git_service import GitService
from diffsage.services.prompt_service import PromptService
from diffsage.services.pull_request_analysis_service import (
    PullRequestAnalysisService,
)
from diffsage.services.pull_request_service import PullRequestService


def create_pull_request_context() -> PullRequestContext:
    return PullRequestContext(
        current_branch="feature/pr-generation",
        base_branch="main",
        merge_base="abc123",
        commits=[
            GitCommit(
                hash="def456",
                author="Test User",
                message="Add PR generation",
                date=datetime(2026, 8, 16, 12, 0, 0),
            )
        ],
        changed_files=[
            "src/diffsage/services/pull_request_service.py",
        ],
        diff="diff --git a/file.py b/file.py",
    )


def create_pull_request_analysis() -> PullRequestAnalysis:
    return PullRequestAnalysis(
        changed_areas=["services"],
        change_categories=[],
        risk_signals=[],
        risk_level=RiskLevel.LOW,
        reviewer_focus=[],
    )


def create_pull_request_draft() -> PullRequestDraft:
    return PullRequestDraft(
        title="Add pull request generation",
        summary="Adds pull request generation.",
        why="Provides structured pull request drafts.",
        changes=[
            "Add pull request orchestration.",
        ],
        testing=[
            "Added unit tests.",
        ],
        risks=[],
        reviewer_focus=[],
        breaking_changes=[],
    )


def create_provider_response() -> ProviderResponse:
    return ProviderResponse(
        content="""{
            "title": "Add pull request generation",
            "summary": "Adds pull request generation.",
            "why": "Provides structured pull request drafts.",
            "changes": ["Add pull request orchestration."],
            "testing": ["Added unit tests."],
            "risks": [],
            "reviewer_focus": [],
            "breaking_changes": []
        }""",
        provider="gemini",
        model="test-model",
        input_tokens=100,
        output_tokens=50,
        finish_reason="stop",
        latency_ms=300,
    )


def create_service() -> tuple[
    PullRequestService,
    Mock,
    Mock,
    Mock,
    Mock,
    Mock,
]:
    git_service = Mock(spec=GitService)
    analysis_service = Mock(spec=PullRequestAnalysisService)
    prompt_service = Mock(spec=PromptService)
    ai_service = Mock(spec=AIService)
    parser = Mock(spec=PullRequestParser)

    service = PullRequestService(
        git_service=git_service,
        analysis_service=analysis_service,
        prompt_service=prompt_service,
        ai_service=ai_service,
        parser=parser,
    )

    return (
        service,
        git_service,
        analysis_service,
        prompt_service,
        ai_service,
        parser,
    )


def test_generate_draft_returns_generated_pull_request_draft() -> None:
    (
        service,
        git_service,
        analysis_service,
        prompt_service,
        ai_service,
        parser,
    ) = create_service()

    context = create_pull_request_context()
    analysis = create_pull_request_analysis()
    response = create_provider_response()
    draft = create_pull_request_draft()

    git_service.build_pull_request_context.return_value = context
    analysis_service.analyze.return_value = analysis
    prompt_service.build_pull_request_prompt.return_value = "generated prompt"
    ai_service.ask.return_value = response
    parser.parse.return_value = draft

    git_service.build_pull_request_context.return_value = context
    analysis_service.analyze.return_value = analysis
    prompt_service.build_pull_request_prompt.return_value = "generated prompt"
    ai_service.ask.return_value = response
    parser.parse.return_value = draft

    result = service.generate_draft("main")

    assert result == draft

    git_service.build_pull_request_context.assert_called_once_with("main")
    analysis_service.analyze.assert_called_once_with(context)
    prompt_service.build_pull_request_prompt.assert_called_once_with(
        context,
        analysis,
    )
    ai_service.ask.assert_called_once_with("generated prompt")
    parser.parse.assert_called_once_with(response.content)


def test_generate_draft_propagates_invalid_pull_request_draft_error() -> None:
    (
        service,
        git_service,
        analysis_service,
        prompt_service,
        ai_service,
        parser,
    ) = create_service()

    context = create_pull_request_context()
    analysis = create_pull_request_analysis()
    response = create_provider_response()

    git_service.build_pull_request_context.return_value = context
    analysis_service.analyze.return_value = analysis
    prompt_service.build_pull_request_prompt.return_value = "generated prompt"
    ai_service.ask.return_value = response

    parser.parse.side_effect = InvalidPullRequestDraftError("Invalid pull request draft.")

    with pytest.raises(InvalidPullRequestDraftError):
        service.generate_draft("main")

    parser.parse.assert_called_once_with(response.content)
