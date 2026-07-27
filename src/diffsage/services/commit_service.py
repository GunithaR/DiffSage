from diffsage.git.client import GitClient
from diffsage.services.ai_service import AIService
from diffsage.services.git_service import GitService
from diffsage.services.prompt_service import PromptService
from diffsage.exceptions.git import NotGitRepositoryError, NoStagedChangesError

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
        response = self._ai_service.ask(prompt)

        return response.content 

