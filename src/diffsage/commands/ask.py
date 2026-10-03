from diffsage.commands.error_handler import handle_command_errors
from diffsage.config.loader import load_settings
from diffsage.config.paths import get_credentials_path
from diffsage.logging.logger import get_logger
from diffsage.services.ai_service import AIService
from diffsage.services.credentials_service import CredentialService
from diffsage.storage.credentials_repository import CredentialsRepository
from diffsage.ui.ask_view import AskView

logger = get_logger(__name__)


@handle_command_errors("ask")
def ask(prompt: str) -> None:
    """Ask the configured AI provider a question"""

    logger.info("Running ask command")
    view = AskView()

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
