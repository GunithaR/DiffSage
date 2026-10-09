import math
import re
import time
from typing import Any

from google import genai
from google.genai import errors as genai_errors
from google.genai import types

from diffsage.config.settings import Settings
from diffsage.exceptions import (
    AuthenticationError,
    ContentBlockedError,
    EmptyResponseError,
    InvalidRequestError,
    ModelNotFoundError,
    ProviderError,
    ProviderUnavailableError,
    RateLimitError,
    ResponseTruncatedError,
)
from diffsage.models.credentials import Credential
from diffsage.models.provider import ProviderRequest, ProviderResponse
from diffsage.providers.base import BaseProvider

# ErrorInfo reason Gemini sends with INVALID_ARGUMENT when the API key is wrong.
INVALID_API_KEY_REASON = "API_KEY_INVALID"


# RetryInfo.retryDelay is a protobuf Duration in JSON form, such as "37s" or "0.5s".
_DURATION = re.compile(r"^(?P<seconds>\d+(?:\.\d+)?)s$")


def _error_details(error: genai_errors.APIError) -> list[dict[str, Any]]:
    """The "details" entries of a Gemini error body.

    Gemini nests them under "error" ({"error": {"details": [...]}}); a bare
    {"details": [...]} body is accepted too.
    """

    body = error.details if isinstance(error.details, dict) else {}
    nested = body.get("error")
    details = (nested if isinstance(nested, dict) else body).get("details")

    if not isinstance(details, list):
        return []

    return [detail for detail in details if isinstance(detail, dict)]


def _error_reasons(error: genai_errors.APIError) -> set[str]:
    """ErrorInfo reasons in a Gemini error body."""

    return {
        detail["reason"]
        for detail in _error_details(error)
        if isinstance(detail.get("reason"), str)
    }


def _retry_after(error: genai_errors.APIError) -> float | None:
    """Seconds Gemini asked us to wait: RetryInfo in the body, else a Retry-After header."""

    for detail in _error_details(error):
        match = _DURATION.match(str(detail.get("retryDelay", "")))

        if match:
            return float(match.group("seconds"))

    headers = getattr(error.response, "headers", None)
    header = headers.get("retry-after") if headers is not None else None

    try:
        return float(header) if header is not None else None
    except ValueError:  # an HTTP date instead of seconds; fall back to our own backoff
        return None


def _rate_limit_message(retry_after: float | None) -> str:
    message = "Gemini API rate limit exceeded."

    if retry_after is None:
        return message

    seconds = math.ceil(retry_after)
    wait = f"{seconds} seconds" if seconds < 120 else f"{math.ceil(seconds / 60)} minutes"

    return f"{message} Gemini asked to wait {wait} before trying again."


def _is_invalid_api_key(error: genai_errors.APIError) -> bool:
    return INVALID_API_KEY_REASON in _error_reasons(error) or "API key not valid" in (
        error.message or ""
    )


# Finish reasons that mean Gemini stopped the reply on purpose (policy or safety).
BLOCKED_FINISH_REASONS = {
    types.FinishReason.SAFETY,
    types.FinishReason.RECITATION,
    types.FinishReason.BLOCKLIST,
    types.FinishReason.PROHIBITED_CONTENT,
    types.FinishReason.SPII,
}


def _reply_text(response: types.GenerateContentResponse, max_tokens: int) -> str:
    """The text of Gemini's reply, or an error saying why there is no usable reply.

    A truncated reply is rejected even when it has text: a commit message or PR
    draft cut off mid-way cannot be parsed reliably.
    """

    feedback = response.prompt_feedback

    if feedback is not None and feedback.block_reason is not None:
        message = f"Gemini blocked the prompt (reason: {feedback.block_reason.value})."

        if feedback.block_reason_message:
            message += f" {feedback.block_reason_message}"

        raise ContentBlockedError(message)

    if not response.candidates:
        raise EmptyResponseError("Gemini returned no reply.")

    candidate = response.candidates[0]
    finish_reason = candidate.finish_reason

    if finish_reason == types.FinishReason.MAX_TOKENS:
        raise ResponseTruncatedError(
            f"Gemini's reply was cut off at the output limit of {max_tokens} tokens."
        )

    if finish_reason in BLOCKED_FINISH_REASONS:
        raise ContentBlockedError(f"Gemini stopped the reply (reason: {finish_reason.value}).")

    parts = candidate.content.parts if candidate.content and candidate.content.parts else []
    # Thinking models return their reasoning as separate "thought" parts; only the
    # answer is wanted.
    text = "".join(part.text for part in parts if part.text and not part.thought)

    if not text.strip():
        raise EmptyResponseError(
            f"Gemini returned an empty reply (finish reason: {finish_reason.value})."
            if finish_reason is not None
            else None
        )

    return text


class GeminiProvider(BaseProvider):
    """Google Gemini provider implementation."""

    def __init__(self, settings: Settings, credential: Credential) -> None:
        self._settings = settings
        self._credential = credential

        self._client = genai.Client(api_key=self._credential.api_key)

    def generate(self, request: ProviderRequest) -> ProviderResponse:
        start_time = time.perf_counter()

        timeout_ms = self._settings.timeout * 1000

        config = types.GenerateContentConfig(
            temperature=request.temperature,
            max_output_tokens=request.max_tokens,
            http_options=types.HttpOptions(timeout=timeout_ms),
        )

        if request.response_schema is not None:
            # Gemini's JSON mode: the reply is a bare JSON document in this shape, with
            # no code fences or surrounding prose.
            config.response_mime_type = "application/json"
            config.response_json_schema = request.response_schema

        try:
            response = self._client.models.generate_content(
                model=request.model, contents=request.prompt, config=config
            )
        except genai_errors.APIError as e:
            status = e.status

            if status == "NOT_FOUND":
                raise ModelNotFoundError(f"Model '{request.model}' was not found.") from e

            elif status == "UNAUTHENTICATED":
                raise AuthenticationError("Authentication with Gemini failed.") from e

            elif status == "INVALID_ARGUMENT":
                if _is_invalid_api_key(e):
                    raise AuthenticationError(
                        "Authentication with Gemini failed. Please check your API Key."
                    ) from e

                # Anything else is a problem with the request itself (prompt too long,
                # unsupported parameter, ...): show Gemini's own explanation.
                raise InvalidRequestError(
                    f"Gemini rejected the request: {e.message}"
                    if e.message
                    else "Gemini rejected the request as invalid."
                ) from e

            elif status == "RESOURCE_EXHAUSTED":
                retry_after = _retry_after(e)

                raise RateLimitError(
                    _rate_limit_message(retry_after), retry_after=retry_after
                ) from e

            elif status in ("UNAVAILABLE", "DEADLINE_EXCEEDED"):
                raise ProviderUnavailableError("Gemini service is currently unavailable.") from e

            raise ProviderError(f"Gemini API request failed: {e}") from e

        latency_ms = round((time.perf_counter() - start_time) * 1000)

        content = _reply_text(response, request.max_tokens)
        # _reply_text guarantees at least one candidate.
        finish_reason = response.candidates[0].finish_reason if response.candidates else None
        usage = response.usage_metadata

        return ProviderResponse(
            content=content,
            provider="gemini",
            model=response.model_version or request.model,
            input_tokens=usage.prompt_token_count if usage else None,
            output_tokens=usage.candidates_token_count if usage else None,
            finish_reason=finish_reason.value if finish_reason else None,
            latency_ms=latency_ms,
        )
