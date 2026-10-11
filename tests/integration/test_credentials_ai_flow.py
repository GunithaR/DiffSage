from pathlib import Path
from unittest.mock import patch

import pytest
from google.genai import types

from diffsage.exceptions import CredentialNotFoundError
from diffsage.models.credentials import Credential
from diffsage.services.ai_service import AIService
from diffsage.services.credentials_service import CredentialService
from diffsage.storage.credentials_repository import CredentialsRepository
from tests.helpers import create_settings


def test_credentials_flow_into_gemini_provider(tmp_path: Path) -> None:
    credential_path = tmp_path / "credentials.toml"

    credential = Credential(
        provider="gemini",
        name="default",
        api_key="test-api-key",
    )

    repository = CredentialsRepository(credential_path)
    repository.save(credential)

    credential_service = CredentialService(repository)
    settings = create_settings()

    mock_response = types.GenerateContentResponse(
        candidates=[
            types.Candidate(
                content=types.Content(role="model", parts=[types.Part(text="Hello from Gemini")]),
                finish_reason=types.FinishReason.STOP,
            )
        ],
        model_version="gemini-3.5-flash-lite",
        usage_metadata=types.GenerateContentResponseUsageMetadata(
            prompt_token_count=10, candidates_token_count=20
        ),
    )

    with patch("diffsage.providers.gemini_provider.genai.Client") as mock_client:
        client = mock_client.return_value
        client.models.generate_content.return_value = mock_response

        service = AIService(
            settings=settings,
            credential_service=credential_service,
        )

        response = service.ask("Hello")

    mock_client.assert_called_once_with(
        api_key="test-api-key",
    )

    request = client.models.generate_content.call_args

    assert request.kwargs["model"] == settings.ai_model
    assert request.kwargs["contents"] == "Hello"

    config = request.kwargs["config"]

    assert config.temperature == 0.2
    assert config.max_output_tokens == 1000

    assert response.content == "Hello from Gemini"
    assert response.provider == "gemini"
    assert response.model == "gemini-3.5-flash-lite"


def test_ai_service_fails_when_default_credential_is_missing(tmp_path: Path) -> None:
    credentials_path = tmp_path / "credentials.toml"

    repository = CredentialsRepository(credentials_path)
    credential_service = CredentialService(repository)
    settings = create_settings()

    with pytest.raises(CredentialNotFoundError):
        AIService(
            settings=settings,
            credential_service=credential_service,
        )
