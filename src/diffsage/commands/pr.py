import json

import typer

from diffsage.commands.error_handler import handle_command_errors
from diffsage.config.loader import load_settings
from diffsage.config.paths import get_credentials_path
from diffsage.exceptions import InvalidPullRequestDraftError
from diffsage.git.client import GitClient
from diffsage.github.client import GitHubClient
from diffsage.logging.logger import get_logger
from diffsage.parsers.pull_request_parser import PullRequestParser
from diffsage.services.ai_service import AIService
from diffsage.services.credentials_service import CredentialService
from diffsage.services.editor_service import EditorService
from diffsage.services.git_service import GitService
from diffsage.services.github_service import GitHubService
from diffsage.services.prompt_service import PromptService
from diffsage.services.pull_request_analysis_service import (
    PullRequestAnalysisService,
)
from diffsage.services.pull_request_service import PullRequestService
from diffsage.storage.credentials_repository import CredentialsRepository
from diffsage.ui.pull_request_view import PullRequestView

logger = get_logger(__name__)


@handle_command_errors("pr")
def pr(
    base_branch: str | None = typer.Argument(
        None,
        help="Base branch to compare against. If omitted, DiffSage resolves it automatically.",
    ),
) -> None:
    """Generate a pull request draft"""

    view = PullRequestView()

    git_client = GitClient()
    github_client = GitHubClient()
    settings = load_settings()

    credential_path = get_credentials_path()
    credential_repository = CredentialsRepository(credential_path)
    credential_service = CredentialService(credential_repository)

    git_service = GitService(git_client)
    github_service = GitHubService(github_client)
    analysis_service = PullRequestAnalysisService()
    prompt_service = PromptService()
    editor_service = EditorService()

    ai_service = AIService(
        settings,
        credential_service,
    )

    parser = PullRequestParser()

    pull_request_service = PullRequestService(
        git_service=git_service,
        analysis_service=analysis_service,
        prompt_service=prompt_service,
        ai_service=ai_service,
        parser=parser,
    )

    resolved_base_branch = git_service.resolve_base_branch(base_branch)
    head_branch = git_service.current_branch()

    git_service.validate_remote_head(head_branch)
    github_service.validate()

    view.show_branches(
        base_branch=resolved_base_branch,
        head_branch=head_branch,
    )

    with view.generating() as status:
        draft = pull_request_service.generate_draft(
            resolved_base_branch,
            on_attempt=lambda attempt, total: status.update(
                f"Generating pull request draft... Attempt {attempt}/{total}"
            ),
            on_notice=view.show_warning,
        )

    view.show_generated(draft)

    while True:
        choice = view.prompt_action()

        if choice in ("", "y"):
            logger.info("User accepted pull request draft.")

            with view.creating():
                pull_request_url = github_service.create_pull_request(
                    draft=draft,
                    base_branch=resolved_base_branch,
                    head_branch=head_branch,
                )

            view.show_created(pull_request_url)
            break

        if choice == "e":
            logger.info("User selected edit.")

            edited_content = editor_service.edit(
                json.dumps(
                    draft.to_dict(),
                    indent=2,
                )
            )

            if edited_content is None:
                view.show_warning("Edit cancelled. The draft is unchanged.")
                continue

            try:
                draft = parser.parse(edited_content)
            except InvalidPullRequestDraftError as e:
                view.show_error(str(e))
                continue

            view.show_generated(draft)
            continue

        if choice == "r":
            logger.info("User selected regenerate.")

            with view.generating():
                draft = pull_request_service.generate_draft(
                    resolved_base_branch,
                    on_attempt=lambda attempt, total: status.update(
                        f"Generating pull request draft... Attempt {attempt}/{total}"
                    ),
                    on_notice=view.show_warning,
                )

            view.show_generated(draft)
            continue

        if choice == "n":
            logger.info("User cancelled pull request generation.")
            view.show_cancelled()
            break

        view.show_invalid_option()
