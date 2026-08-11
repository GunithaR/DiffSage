from diffsage.exceptions import NoStagedChangesError, NotGitRepositoryError
from diffsage.git.client import GitClient
from diffsage.logging.logger import get_logger
from diffsage.services.ai_service import AIService
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

    def generate_commit_message(self) -> str:
        if not self._git_client.is_git_repository():
            raise NotGitRepositoryError

        if not self._git_client.staged_diff():
            raise NoStagedChangesError

        context = self._git_service.build_commit_context()
        prompt = self._prompt_service.build_commit_prompt(context)

        logger.info("Generating commit message.")
        response = self._ai_service.ask(prompt)
        logger.info("Commit message generated successfully.")

        return response.content
