"""End-to-end tests for `diffsage ask`: real CLI, fake AI provider."""

import pytest
from typer.testing import CliRunner

from diffsage.cli import app
from diffsage.commands.error_handler import UNEXPECTED_ERROR_MESSAGE
from diffsage.exceptions import (
    InvalidRequestError,
    ProviderError,
    RateLimitError,
    ResponseTruncatedError,
)

runner = CliRunner()


def test_ask_prints_provider_response(fake_provider) -> None:
    fake_provider.queue("Rebase rewrites history; merge preserves it.")

    result = runner.invoke(app, ["ask", "rebase or merge?"])

    assert result.exit_code == 0, result.output
    assert "Rebase rewrites history; merge preserves it." in result.output
    assert fake_provider.prompts == ["rebase or merge?"]


@pytest.mark.parametrize(
    "error",
    [
        # Not retried: the wait asked for is longer than DiffSage is willing to wait.
        RateLimitError("Gemini API rate limit exceeded.", retry_after=3600),
        ProviderError("Gemini API request failed: 500 INTERNAL."),
        InvalidRequestError("Gemini rejected the request: The input token count is too large."),
        ResponseTruncatedError("Gemini's reply was cut off at the output limit of 1000 tokens."),
    ],
)
def test_ask_reports_provider_errors_instead_of_unexpected_error(fake_provider, error) -> None:
    """Regression: before the shared handler, `ask` reported these as unexpected errors."""

    fake_provider.queue(error)

    result = runner.invoke(app, ["ask", "hello"])

    assert result.exit_code == 1
    assert f"✗ {error}" in result.output
    assert UNEXPECTED_ERROR_MESSAGE not in result.output


def test_ask_recovers_from_a_rate_limit_by_retrying(fake_provider) -> None:
    fake_provider.queue(RateLimitError("Gemini API rate limit exceeded."), "Recovered answer.")

    result = runner.invoke(app, ["ask", "hello"])

    assert result.exit_code == 0, result.output
    assert "Recovered answer." in result.output
    assert fake_provider.prompts == ["hello", "hello"]


def test_truncated_reply_says_how_to_raise_the_limit(fake_provider) -> None:
    fake_provider.queue(ResponseTruncatedError("The reply was cut off at 1000 tokens."))

    result = runner.invoke(app, ["ask", "hello"])

    assert result.exit_code == 1
    assert "diffsage config set max_output_tokens <tokens>" in " ".join(result.output.split())
