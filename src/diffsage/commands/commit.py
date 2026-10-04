from collections.abc import Callable

from diffsage.commands.error_handler import handle_command_errors
from diffsage.config.loader import load_settings
from diffsage.config.paths import get_credentials_path
from diffsage.exceptions import InvalidCommitMessageError
from diffsage.git.client import GitClient
from diffsage.logging.logger import get_logger
from diffsage.parsers.commit_message_parser import CommitMessageParser
from diffsage.services.ai_service import AIService
from diffsage.services.commit_service import CommitService
from diffsage.services.credentials_service import CredentialService
from diffsage.services.editor_service import EditorService
from diffsage.services.git_service import GitService
from diffsage.services.prompt_service import PromptService
from diffsage.storage.credentials_repository import CredentialsRepository
from diffsage.ui.commit_view import CommitView

logger = get_logger(__name__)


def generate_message(
    commit_service: CommitService,
    on_attempt: Callable[[int, int], None] | None = None,
    on_notice: Callable[[str], None] | None = None,
) -> str:
    return commit_service.generate_commit_message(
        on_attempt=on_attempt,
        on_notice=on_notice,
    )


@handle_command_errors("commit")
def commit() -> None:
    """Generate a conventional commit message"""

    git_client = GitClient()
    view = CommitView()
    editor = EditorService()

    settings = load_settings()

    credential_path = get_credentials_path()
    credential_repository = CredentialsRepository(credential_path)
    credential_service = CredentialService(credential_repository)

    git_service = GitService(git_client)
    ai_service = AIService(
        settings,
        credential_service,
    )
    prompt_service = PromptService()

    commit_service = CommitService(
        git_client,
        git_service,
        prompt_service,
        ai_service,
    )

    with view.generating() as status:
        raw_message = generate_message(
            commit_service,
            on_attempt=lambda attempt, total: status.update(
                f"Generating commit message... Attempt {attempt}/{total}"
            ),
            on_notice=view.show_warning,
        )
        commit_message = CommitMessageParser.parse(raw_message)

    view.show_generated()
    view.show_commit(commit_message)

    # Text of an edit that did not parse; the next E reopens it so nothing typed is lost.
    pending_edit: str | None = None

    while True:
        choice = view.prompt_action()

        if choice in ("", "y"):
            logger.info("User selected commit.")
            # Commit the cleaned message: no code fences or preamble from the AI reply.
            message_text = commit_message.to_text()
            git_client.commit(message_text)
            view.show_success(message_text)
            break

        if choice == "e":
            logger.info("User selected edit.")
            edited = editor.edit(pending_edit or commit_message.to_text())

            try:
                commit_message = CommitMessageParser.parse(edited)
            except InvalidCommitMessageError as error:
                pending_edit = edited
                view.show_error(error.message)
                view.show_warning(
                    "Your edit was kept. Press E to continue editing it. The message below "
                    "is unchanged, and Y commits it."
                )
            else:
                pending_edit = None

            view.show_commit(commit_message)
            continue

        if choice == "r":
            logger.info("User selected regenerate.")
            with view.generating() as status:
                raw_message = generate_message(
                    commit_service,
                    on_attempt=lambda attempt, total: status.update(
                        f"Generating commit message... Attempt {attempt}/{total}"
                    ),
                    on_notice=view.show_warning,
                )

            try:
                commit_message = CommitMessageParser.parse(raw_message)
            except InvalidCommitMessageError as error:
                view.show_error(error.message)
                view.show_warning(
                    "The new suggestion could not be used. The message below is unchanged."
                )
            else:
                pending_edit = None
                view.show_generated()

            view.show_commit(commit_message)
            continue

        if choice == "n":
            logger.info("User cancelled commit.")
            view.show_cancelled()
            break

        view.show_invalid_option()
