from collections.abc import Callable

from diffsage.models.pull_request import PullRequestDraft
from diffsage.parsers.pull_request_parser import PullRequestParser
from diffsage.services.ai_service import AIService
from diffsage.services.git_service import GitService
from diffsage.services.prompt_service import PromptService
from diffsage.services.pull_request_analysis_service import PullRequestAnalysisService


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
    ) -> PullRequestDraft:
        context = self._git_service.build_pull_request_context(base_branch)

        analysis = self._analysis_service.analyze(context)

        prompt = self._prompt_service.build_pull_request_prompt(
            context,
            analysis,
        )

        response = self._ai_service.ask(
            prompt, 
            on_attempt=on_attempt
        )

        return self._parser.parse(response.content)
