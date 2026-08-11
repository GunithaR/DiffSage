from unittest.mock import patch

from diffsage.models.credentials import Credential
from diffsage.providers.factory import create_provider
from tests.helpers import create_settings


def test_create_provider_creates_gemini_provider_with_credential() -> None:
    settings = create_settings()

    credential = Credential(
        provider="gemini",
        name="defauly",
        api_key="test-api-key",
    )

    with patch("diffsage.providers.factory.GeminiProvider") as mock_provider:
        create_provider(
            settings,
            credential,
        )

        mock_provider.assert_called_once_with(
            settings,
            credential,
        )
