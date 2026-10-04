from collections.abc import Callable
from dataclasses import replace

from diffsage.exceptions import NoStagedChangesError, NotGitRepositoryError
from diffsage.git.client import GitClient
from diffsage.logging.logger import get_logger
from diffsage.services.ai_service import AIService
from diffsage.services.diff_sanitizer import sanitize
from diffsage.services.git_service import GitService
from diffsage.services.prompt_service import PromptService

logger = get_logger(__name__)


class CommitService:
    def __init__(
        self,
        git_client: GitClient,
        git_service: GitService,
        prompt_service: PromptService,
        ai_service: AIService,
    ) -> None:
        self._git_client = git_client
        self._git_service = git_service
        self._prompt_service = prompt_service
        self._ai_service = ai_service

    def generate_commit_message(
        self,
        on_attempt: Callable[[int, int], None] | None = None,
        on_notice: Callable[[str], None] | None = None,
    ) -> str:
        if not self._git_client.is_git_repository():
            raise NotGitRepositoryError

        if not self._git_client.staged_diff():
            raise NoStagedChangesError

        context = self._git_service.build_commit_context()

        staged = sanitize(context.staged_diff)
        context = replace(context, staged_diff=staged.text)
        notes = staged.notices()

        for note in notes:
            logger.info("Diff sanitized: %s", note)

            if on_notice is not None:
                on_notice(note)

        prompt = self._prompt_service.build_commit_prompt(context, notes)

        logger.info("Generating commit message.")
        response = self._ai_service.ask(
            prompt,
            on_attempt=on_attempt,
        )
        logger.info("Commit message generated successfully.")

        return response.content
