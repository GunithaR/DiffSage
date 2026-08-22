import json

import typer

from diffsage.config.loader import load_settings
from diffsage.config.paths import get_credentials_path
from diffsage.exceptions import (
    BaseBranchNotFoundError,
    ConfigError,
    CredentialNotFoundError,
    DetachedHeadError,
    GitHubAuthenticationError,
    GitHubCLIUnavailableError,
    InvalidPullRequestDraftError,
    NotGitRepositoryError,
    ProviderError,
    RemoteBranchNotFoundError,
    SameBranchError,
    UnpushedChangesError,
)
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


def pr(
    base_branch: str | None = typer.Argument(
        None,
        help="Base branch to compare against. If omitted, DiffSage resolves it automatically.",
    ),
) -> None:
    """Generate a pull request draft"""

    view = PullRequestView()

    try:
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

        with view.generating():
            draft = pull_request_service.generate_draft(
                resolved_base_branch,
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
                    )

                view.show_generated(draft)
                continue

            if choice == "n":
                logger.info("User cancelled pull request generation.")
                view.show_cancelled()
                break

            view.show_invalid_option()

    except NotGitRepositoryError:
        logger.info("Command aborted: not a Git repository.")
        view.show_not_git_repository()
        raise SystemExit(1) from None

    except DetachedHeadError:
        logger.info("Command aborted: detached HEAD.")
        view.show_detached_head()
        raise SystemExit(1) from None

    except BaseBranchNotFoundError:
        logger.info("Command aborted: base branch could not be determined.")
        view.show_base_branch_not_found()
        raise SystemExit(1) from None

    except SameBranchError:
        logger.info("Current branch and base branch are the same.")
        view.show_same_branch()
        raise SystemExit(1) from None

    except RemoteBranchNotFoundError:
        logger.info("Command aborted: remote branch does not exist.")
        view.show_error("Remote branch does not exist on origin.")
        raise SystemExit(1) from None

    except UnpushedChangesError:
        logger.info("Command aborted: branch contains unpushed commits.")
        view.show_error("Your branch contains commits that have not been pushed to origin.")
        raise SystemExit(1) from None

    except ProviderError as e:
        logger.warning(str(e))
        view.show_error(str(e))
        raise SystemExit(1) from None

    except CredentialNotFoundError as e:
        logger.warning(str(e))
        view.show_error(str(e))
        raise SystemExit(1) from None

    except ConfigError as e:
        logger.warning(str(e))
        view.show_error(str(e))
        raise SystemExit(1) from None

    except InvalidPullRequestDraftError as e:
        logger.warning(str(e))
        view.show_error(str(e))
        raise SystemExit(1) from None

    except GitHubCLIUnavailableError as e:
        logger.warning(str(e))
        view.show_error(str(e))
        raise SystemExit(1) from None

    except GitHubAuthenticationError as e:
        logger.warning(str(e))
        view.show_error(str(e))
        raise SystemExit(1) from None

    except Exception:
        logger.exception("Unexpected error while executing PR command.")
        view.show_error("An unexpected error occurred. Please check the log file for more details.")
        raise SystemExit(1) from None
