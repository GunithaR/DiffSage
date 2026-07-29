from diffsage.config.loader import load_settings
from diffsage.exceptions.base import ConfigError
from diffsage.exceptions.git import (
    NotGitRepositoryError, 
    NoStagedChangesError,
)
from diffsage.exceptions.provider import ProviderError
from diffsage.git.client import GitClient
from diffsage.services.ai_service import AIService
from diffsage.services.commit_service import CommitService
from diffsage.services.editor import EditorService
from diffsage.services.git_service import GitService
from diffsage.services.prompt_service import PromptService
from diffsage.ui.commit_view import CommitView
from diffsage.parsers.commit_message_parse import CommitMessageParser
from diffsage.logging.logger import get_logger

logger = get_logger(__name__)


def generate_message(commit_service: CommitService) -> str:
    return commit_service.generate_commit_message()

def commit() -> None:
    try:
        git_client = GitClient()
        view = CommitView()
        editor = EditorService()

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

        with view.generating():
            raw_message = generate_message(commit_service)
            commit_message = CommitMessageParser.parse(raw_message)

        view.show_generated()
        view.show_commit(commit_message)

        while True:
            choice = view.prompt_action()

            if choice in ("", "y"):
                logger.info("User selected commit.")
                git_client.commit(raw_message)
                view.show_success(raw_message)
                break

            if choice == "e":
                logger.info("User selected edit.")
                raw_message = editor.edit(raw_message)
                commit_message = CommitMessageParser.parse(raw_message)
                view.show_commit(commit_message)
                continue

            if choice == "r":
                logger.info("User selected regenerate.")
                with view.generating():
                    raw_message = generate_message(commit_service)
                    commit_message = CommitMessageParser.parse(raw_message)

                view.show_generated()
                view.show_commit(commit_message)
                continue

            if choice == "n":
                logger.info("User cancelled commit.")
                view.show_cancelled()
                break

            view.show_invalid_option()

    except NotGitRepositoryError:
        logger.info("Command aborted: not a Git repository.")
        view.show_not_git_repository()
        raise SystemExit(1)

    except NoStagedChangesError:
        logger.info("Command aborted: no staged changes.")
        view.show_no_staged_changes()
        raise SystemExit(1)

    except ProviderError as e:
        logger.warning(str(e))
        view.show_error(str(e))    
        raise SystemExit(1)

    except ConfigError as e:
        logger.warning(str(e))
        view.show_error(str(e))    
        raise SystemExit(1)

    except Exception:
        logger.exception("Unexpected error while executing commit command.")
        view.show_error(
            "An unexpected error occurred. Please check the log file for more details."
        )
        raise SystemExit(1)

    