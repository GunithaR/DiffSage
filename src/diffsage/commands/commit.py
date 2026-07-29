from rich.console import Console

from diffsage.config.loader import load_settings
from diffsage.exceptions.git import (
    NotGitRepositoryError, 
    NoStagedChangesError,
)
from diffsage.git.client import GitClient
from diffsage.services.ai_service import AIService
from diffsage.services.commit_service import CommitService
from diffsage.services.editor import EditorService
from diffsage.services.git_service import GitService
from diffsage.services.prompt_service import PromptService
from diffsage.ui.commit_view import CommitView


console = Console()


def generate_message(commit_service: CommitService, view: CommitView) -> str:
    try:
        return commit_service.generate_commit_message()

    except NotGitRepositoryError:
        view.show_not_git_repository()
        raise SystemExit(1)

    except NoStagedChangesError:
        view.show_no_staged_changes()
        raise SystemExit(1)

def commit() -> None:
    git_client = GitClient()

    settings = load_settings()

    git_service = GitService(git_client)
    ai_service = AIService(settings)
    prompt_service = PromptService()

    commit_service = CommitService(
        git_client,
        git_service,
        prompt_service,
        ai_service,
    )

    editor = EditorService()
    view = CommitView()

    with view.generating():
        message = generate_message(commit_service, view)

    view.show_generated()
    view.show_commit(message)

    while True:
        choice = view.prompt_action()

        if choice in ("", "y"):
            git_client.commit(message)
            view.show_success(message)
            break

        if choice == "e":
            message = editor.edit(message)
            view.show_commit(message)
            continue

        if choice == "r":
            with view.generating():
                message = generate_message(commit_service, view)

            view.show_generated()
            view.show_commit(message)
            continue

        if choice == "n":
            view.show_cancelled()
            break

        view.show_invalid_option()