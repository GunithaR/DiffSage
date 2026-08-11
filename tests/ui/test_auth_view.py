from io import StringIO

from rich.console import Console

from diffsage.models.credentials import Credential
from diffsage.ui.auth_view import AuthView


def test_mask_api_key() -> None:
    assert AuthView._mask_api_key("abcdefghijklmnop") == "abcd••••••••mnop"


def test_mask_short_api_key() -> None:
    assert AuthView._mask_api_key("abc") == "••••••••"


def test_show_credential_masks_api_key() -> None:
    view = AuthView()

    output = StringIO()
    view._console = Console(file=output)

    credential = Credential(
        provider="gemini",
        name="default",
        api_key="abcdefghijklmnop",
    )

    view.show_credential(credential)

    rendered = output.getvalue()

    assert "gemini" in rendered
    assert "default" in rendered
    assert "abcd••••••••mnop" in rendered
    assert "abcdefghijklmnop" not in rendered


def test_show_credentials_does_not_display_api_keys() -> None:
    view = AuthView()

    output = StringIO()
    view._console = Console(file=output)

    credentials = [
        Credential(
            provider="gemini",
            name="default",
            api_key="gemini-secret",
        ),
        Credential(
            provider="openai",
            name="paid",
            api_key="openai-secret",
        ),
    ]

    view.show_credentials(credentials)

    rendered = output.getvalue()

    assert "gemini" in rendered
    assert "default" in rendered
    assert "openai" in rendered
    assert "paid" in rendered

    assert "gemini-secret" not in rendered
    assert "openai-secret" not in rendered
