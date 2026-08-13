from diffsage.config.loader import load_settings
from diffsage.config.paths import get_credentials_path
from diffsage.exceptions import (
    AuthenticationError,
    ConfigError,
    CredentialNotFoundError,
    ModelNotFoundError,
    ProviderUnavailableError,
)
from diffsage.logging.logger import get_logger
from diffsage.services.ai_service import AIService
from diffsage.services.credentials_service import CredentialService
from diffsage.storage.credentials_repository import CredentialsRepository
from diffsage.ui.ask_view import AskView

logger = get_logger(__name__)


def ask(prompt: str) -> None:
    """Ask the configured AI provider a question"""

    logger.info("Running ask command")
    view = AskView()

    try:
        settings = load_settings()

        credential_path = get_credentials_path()
        repository = CredentialsRepository(credential_path)
        credential_service = CredentialService(repository)

        service = AIService(
            settings,
            credential_service,
        )

        response = service.ask(prompt)
        view.show_response(response)

    except AuthenticationError as e:
        logger.warning(str(e))
        view.show_error(str(e))
        raise SystemExit(1) from None

    except CredentialNotFoundError as e:
        logger.warning(str(e))
        view.show_error(str(e))
        raise SystemExit(1) from None

    except ModelNotFoundError as e:
        logger.warning(str(e))
        view.show_error(str(e))
        raise SystemExit(1) from None

    except ProviderUnavailableError as e:
        logger.warning(str(e))
        view.show_error(str(e))
        raise SystemExit(1) from None

    except ConfigError as e:
        logger.warning(str(e))
        view.show_error(str(e))
        raise SystemExit(1) from None

    except Exception:
        logger.exception("Unexpected error while executing ask command.")
        view.show_error("An unexpected error occurred. Please check the log file for more details.")
        raise SystemExit(1) from None
