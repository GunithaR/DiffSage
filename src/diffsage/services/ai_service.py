import random
import time
from collections.abc import Callable
from typing import Any

from diffsage.config.settings import Settings
from diffsage.exceptions import ProviderUnavailableError, RateLimitError
from diffsage.models.provider import ProviderRequest, ProviderResponse
from diffsage.providers.base import BaseProvider
from diffsage.providers.factory import create_provider
from diffsage.services.credentials_service import CredentialService

# Longest wait between attempts when the provider does not say how long to wait.
MAX_BACKOFF_SECONDS = 30
# A provider asking for a longer wait than this (typically a used-up daily quota) is not
# retried: the command fails at once with the provider's suggested wait instead of hanging.
MAX_SUGGESTED_WAIT_SECONDS = 60


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

    def _ask_once(
        self, prompt: str, response_schema: dict[str, Any] | None = None
    ) -> ProviderResponse:
        request = ProviderRequest(
            prompt=prompt,
            model=self._settings.ai_model,
            temperature=0.2,
            max_tokens=1000,
            response_schema=response_schema,
        )

        return self._provider.generate(request)

    def _backoff_delay(self, attempt: int) -> float:
        """Exponential backoff (1s, 2s, 4s, ... up to MAX_BACKOFF_SECONDS) with jitter.

        The delay is picked at random between half and all of the step, so several
        clients that failed together do not all retry at the same moment.
        """

        step = min(2**attempt, MAX_BACKOFF_SECONDS)
        return random.uniform(step / 2, step)

    def _retry_delay(self, attempt: int, error: Exception) -> float | None:
        """Seconds to wait before the next attempt, or None if retrying is pointless."""

        if isinstance(error, RateLimitError) and error.retry_after is not None:
            if error.retry_after > MAX_SUGGESTED_WAIT_SECONDS:
                return None

            return error.retry_after

        return self._backoff_delay(attempt)

    def ask(
        self,
        prompt: str,
        on_attempt: Callable[[int, int], None] | None = None,
        response_schema: dict[str, Any] | None = None,
    ) -> ProviderResponse:
        """Send `prompt` to the provider, retrying outages and rate limits.

        `response_schema` (a JSON Schema) asks for a reply in that JSON shape.
        """

        total_attempts = self._settings.max_retries + 1
        attempt = 0

        # Every pass returns, raises, or sleeps and tries again; `while True` lets type
        # checkers see that the method never falls off the end without a response.
        while True:
            attempt_number = attempt + 1

            if on_attempt is not None:
                on_attempt(attempt_number, total_attempts)

            try:
                return self._ask_once(prompt, response_schema)

            except (ProviderUnavailableError, RateLimitError) as error:
                delay = self._retry_delay(attempt, error)

                if attempt_number >= total_attempts or delay is None:
                    raise

                time.sleep(delay)
                attempt += 1
