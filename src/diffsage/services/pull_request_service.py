from collections.abc import Callable
from dataclasses import replace

from diffsage.logging.logger import get_logger
from diffsage.models.pull_request import PullRequestDraft
from diffsage.parsers.pull_request_parser import (
    PULL_REQUEST_DRAFT_SCHEMA,
    TEMPLATED_DRAFT_SCHEMA,
    PullRequestParser,
)
from diffsage.services.ai_service import AIService
from diffsage.services.diff_sanitizer import sanitize
from diffsage.services.git_service import GitService
from diffsage.services.prompt_service import PromptService
from diffsage.services.pull_request_analysis_service import PullRequestAnalysisService

logger = get_logger(__name__)


class PullRequestService:
    def __init__(
        self,
        git_service: GitService,
        analysis_service: PullRequestAnalysisService,
        prompt_service: PromptService,
        ai_service: AIService,
        parser: PullRequestParser,
    ) -> None:
        self._git_service = git_service
        self._analysis_service = analysis_service
        self._prompt_service = prompt_service
        self._ai_service = ai_service
        self._parser = parser

    def generate_draft(
        self,
        base_branch: str,
        on_attempt: Callable[[int, int], None] | None = None,
        on_notice: Callable[[str], None] | None = None,
        base_ref: str | None = None,
        on_info: Callable[[str], None] | None = None,
    ) -> PullRequestDraft:
        context = self._git_service.build_pull_request_context(base_branch, base_ref)
        template = self._git_service.pull_request_template(base_ref or base_branch)

        if template is not None:
            logger.info("Using pull request template %s", template[0])

            if on_info is not None:
                on_info(f"Filling in the repository's pull request template ({template[0]}).")

        analysis = self._analysis_service.analyze(context)

        sanitized = sanitize(context.diff)
        context = replace(context, diff=sanitized.text)
        notes = sanitized.notices()

        for note in notes:
            logger.info("Diff sanitized: %s", note)

            if on_notice is not None:
                on_notice(note)

        prompt = self._prompt_service.build_pull_request_prompt(
            context,
            analysis,
            notes,
            template=template[1] if template else None,
        )

        response = self._ai_service.ask(
            prompt,
            on_attempt=on_attempt,
            response_schema=TEMPLATED_DRAFT_SCHEMA if template else PULL_REQUEST_DRAFT_SCHEMA,
        )

        return self._parser.parse(response.content)
