import time
from collections.abc import Callable

from diffsage.config.settings import Settings
from diffsage.exceptions import ProviderUnavailableError
from diffsage.models.provider import ProviderRequest, ProviderResponse
from diffsage.providers.base import BaseProvider
from diffsage.providers.factory import create_provider
from diffsage.services.credentials_service import CredentialService


class AIService:
    """Coordinates AI provider interactions."""

    def __init__(
        self,
        settings: Settings,
        credential_service: CredentialService,
        provider: BaseProvider | None = None,
    ) -> None:
        self._settings = settings

        if provider is not None:
            self._provider = provider
        else:
            credential = credential_service.resolve_credential(
                settings.provider, settings.credential_profile
            )

            self._provider = create_provider(settings, credential)

    def _ask_once(self, prompt: str) -> ProviderResponse:
        request = ProviderRequest(
            prompt=prompt,
            model=self._settings.ai_model,
            temperature=0.2,
            max_tokens=1000,
        )

        return self._provider.generate(request)

    def _backoff_delay(self, attempt: int) -> int:
        return 2**attempt

    def ask(
        self,
        prompt: str,
        on_attempt: Callable[[int, int], None] | None = None,
    ) -> ProviderResponse:
        total_attempts = self._settings.max_retries + 1

        for attempt in range(total_attempts):
            attempt_number = attempt + 1

            if on_attempt is not None:
                on_attempt(attempt_number, total_attempts)

            try:
                return self._ask_once(prompt)

            except ProviderUnavailableError:
                if attempt == total_attempts - 1:
                    raise

                delay = self._backoff_delay(attempt)
                time.sleep(delay)
