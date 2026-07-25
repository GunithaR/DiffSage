import typer

from diffsage.logging.logger import get_logger
from diffsage.services.ai_service import AIService

logger = get_logger(__name__)

def ask(prompt: str) -> None:
    "Ask the configured AI provider a question"

    logger.info("Running ask command")

    service = AIService()

    response = service.ask(prompt)

    typer.echo()
    typer.echo(response.content)