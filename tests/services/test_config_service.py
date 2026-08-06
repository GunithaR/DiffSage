from unittest.mock import Mock, patch

import pytest

from diffsage.exceptions import InvalidConfigurationValueError, UnknownConfigurationKeyError
from diffsage.services.config_service import ConfigService
from diffsage.storage.config_repository import ConfigRepository
from tests.helpers import create_settings


def test_get_configuration_returns_config_report() -> None:
    settings = create_settings(
        provider="gemini",
        ai_model="gemini-3.5-flash-lite",
        timeout=60,
        max_retries=3,
        log_level="INFO",
    )

    repository = Mock(spec=ConfigRepository)
    service = ConfigService(settings, repository)
    report = service.get_configuration()

    assert report.provider == settings.provider
    assert report.model == settings.ai_model
    assert report.timeout == settings.timeout
    assert report.max_retries == settings.max_retries
    assert report.log_level == settings.log_level

def test_get_value_returns_requested_configuration() -> None:
    settings = create_settings(
        provider="gemini",
        ai_model="gemini-3.5-flash-lite",
        timeout=60,
        max_retries=3,
        log_level="INFO",
    )

    repository = Mock(spec=ConfigRepository)
    service = ConfigService(settings, repository)
    report = service.get_value("provider")

    assert report.key == "provider"
    assert report.value == settings.provider


def test_get_value_unknown_key_raises_error() -> None:
    settings = create_settings(
        provider="gemini",
        ai_model="gemini-3.5-flash-lite",
        timeout=60,
        max_retries=3,
        log_level="INFO",
    )

    repository = Mock(spec=ConfigRepository)
    service = ConfigService(settings, repository)

    with pytest.raises(UnknownConfigurationKeyError) as exception_info:
        service.get_value("invalid")

    assert "invalid" in str(exception_info.value)


def test_set_value_returns_updated_configuration() -> None:
    settings = create_settings(
        provider="gemini",
        ai_model="gemini-3.5-flash-lite",
    )

    updated_settings = create_settings(
        provider="openai",
        ai_model="gpt-5",
    )

    repository = Mock(spec=ConfigRepository)
    service = ConfigService(settings, repository)

    with patch(
        "diffsage.services.config_service.load_settings", return_value=updated_settings
    ) as mock_load_settings:

        report = service.set_value(
            "provider",
            "openai",
        )

    repository.set.assert_called_once_with(
        "provider",
        "openai",
    )
    mock_load_settings.assert_called_once()
    assert report.provider == updated_settings.provider
    assert report.timeout == updated_settings.timeout
    assert report.max_retries == updated_settings.max_retries
    assert report.model == updated_settings.ai_model
    assert report.log_level == updated_settings.log_level


def test_set_value_converts_integer_values() -> None:
    settings = create_settings(
        timeout=30,
    )

    repository = Mock(spec=ConfigRepository)
    service = ConfigService(settings, repository)

    with patch("diffsage.services.config_service.load_settings", return_value=settings):
        service.set_value(
            "timeout",
            "120",
        )

    repository.set.assert_called_once_with(
        "timeout",
        120,
    )


def test_set_value_invalid_integer_raises_error() -> None:
    settings = create_settings(
        timeout=30,
    )

    repository = Mock(spec=ConfigRepository)
    service = ConfigService(settings, repository)

    with pytest.raises(InvalidConfigurationValueError):
        service.set_value(
            "timeout",
            "abc"
        )

    repository.set.assert_not_called()


def test_set_value_normalizes_input() -> None:
    settings = create_settings(
        provider="gemini"
    )

    updated_settings = create_settings(
        provider="openai"
    )

    repository = Mock(spec=ConfigRepository)
    service = ConfigService(settings, repository)

    with patch("diffsage.services.config_service.load_settings", return_value=updated_settings):
        report = service.set_value(
            "provider",
            " OPENAI ",
        )

    repository.set.assert_called_once_with(
        "provider",
        "openai",
    )
    assert report.provider == updated_settings.provider


def test_set_value_unknown_key_raises_error() -> None:
    settings = create_settings(
        timeout=30,
    )

    repository = Mock(spec=ConfigRepository)
    service = ConfigService(settings, repository)

    with pytest.raises(UnknownConfigurationKeyError):
        service.set_value(
            "invalid_key",
            "value",
        )

    repository.set.assert_not_called()


def test_unset_value_returns_updated_configuration() -> None:
    settings = create_settings(
        provider="gemini",
        ai_model="gemini-3.5-flash-lite",
    )

    updated_settings = create_settings(
        provider="gemini",
    )

    repository = Mock(spec=ConfigRepository)
    service = ConfigService(settings, repository)

    with patch(
        "diffsage.services.config_service.load_settings", 
        return_value=updated_settings,
    ) as mock_load_settings:

        report = service.unset_value("model")

    mock_load_settings.assert_called_once()
    repository.unset.assert_called_once_with("model")
    assert report.provider == updated_settings.provider
    assert report.model == updated_settings.ai_model
    assert report.timeout == updated_settings.timeout
    assert report.max_retries == updated_settings.max_retries
    assert report.log_level == updated_settings.log_level


def test_unset_value_unknown_key_raises_error() -> None:
    settings = create_settings(
        provider="gemini",
        ai_model="gemini-3.5-flash-lite",
    )

    repository = Mock(spec=ConfigRepository)
    service = ConfigService(settings, repository)

    with pytest.raises(UnknownConfigurationKeyError) as exception_info:
        service.unset_value("invalid_key")

    repository.unset.assert_not_called()
    assert "invalid_key" in str(exception_info.value)