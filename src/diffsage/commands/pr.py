import typer

from diffsage.config.loader import load_settings
from diffsage.config.paths import get_credentials_path
from diffsage.exceptions import (
    BaseBranchNotFoundError,
    ConfigError,
    CredentialNotFoundError,
    DetachedHeadError,
    NotGitRepositoryError,
    ProviderError,
    SameBranchError,
)
from diffsage.git.client import GitClient
from diffsage.logging.logger import get_logger
from diffsage.parsers.pull_request_parser import PullRequestParser
from diffsage.services.ai_service import AIService
from diffsage.services.credentials_service import CredentialService
from diffsage.services.git_service import GitService
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
        settings = load_settings()

        credential_path = get_credentials_path()
        credential_repository = CredentialsRepository(credential_path)
        credential_service = CredentialService(credential_repository)

        git_service = GitService(git_client)
        analysis_service = PullRequestAnalysisService()
        prompt_service = PromptService()

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

        with view.generating():
            draft = pull_request_service.generate_draft(
                resolved_base_branch,
            )

        view.show_generated(draft)

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

    except Exception:
        logger.exception("Unexpected error while executing PR command.")
        view.show_error("An unexpected error occurred. Please check the log file for more details.")
        raise SystemExit(1) from None
