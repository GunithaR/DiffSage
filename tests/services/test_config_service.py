from unittest.mock import Mock, patch

import pytest

from diffsage.exceptions import (
    ConfigError,
    InvalidConfigurationValueError,
    UnknownConfigurationKeyError,
)
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


def test_get_raw_configuration_returns_config_report() -> None:
    settings = create_settings(
        provider="gemini",
        ai_model="gemini-3.5-flash-lite",
        timeout=60,
        max_retries=3,
        log_level="INFO",
    )

    repository = Mock(spec=ConfigRepository)
    repository.list.return_value = {
        "provider": "gemini",
        "model": "gemini-3.5-flash-lite",
        "timeout": 30,
        "max_retries": 3,
        "log_level": "INFO",
    }

    service = ConfigService(settings, repository)
    report = service.get_configuration_raw()

    repository.list.assert_called_once()

    assert report.provider == "gemini"
    assert report.model == "gemini-3.5-flash-lite"
    assert report.timeout == 30
    assert report.max_retries == 3
    assert report.log_level == "INFO"


def test_get_raw_configuration_returns_missing_values() -> None:
    settings = create_settings(
        provider="gemini",
        ai_model="gemini-3.5-flash-lite",
        timeout=60,
        max_retries=3,
        log_level="INFO",
    )

    repository = Mock(spec=ConfigRepository)
    repository.list.return_value = {
        "provider": "gemini",
    }

    service = ConfigService(settings, repository)
    report = service.get_configuration_raw()

    assert report.provider == "gemini"
    assert report.model is None
    assert report.timeout is None
    assert report.max_retries is None
    assert report.log_level is None


def test_get_raw_value_returns_requested_configuration() -> None:
    settings = create_settings(
        provider="gemini",
        ai_model="gemini-3.5-flash-lite",
        timeout=60,
        max_retries=3,
        log_level="INFO",
    )

    repository = Mock(spec=ConfigRepository)
    repository.get.return_value = "gemini"

    service = ConfigService(settings, repository)
    report = service.get_configuration_value_raw("provider")

    repository.get.assert_called_once_with("provider")

    assert report.key == "provider"
    assert report.value == "gemini"


def test_get_raw_value_unknown_key_raises_error() -> None:
    settings = create_settings(
        provider="gemini",
        ai_model="gemini-3.5-flash-lite",
        timeout=60,
        max_retries=3,
        log_level="INFO",
    )

    repository = Mock(spec=ConfigRepository)
    service = ConfigService(settings, repository)

    with pytest.raises(UnknownConfigurationKeyError):
        service.get_configuration_value_raw("invalid")

    repository.get.assert_not_called()


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
        provider="gemini",
        ai_model="gemini-2.5-pro",
    )

    repository = Mock(spec=ConfigRepository)
    service = ConfigService(settings, repository)

    with patch(
        "diffsage.services.config_service.load_settings", return_value=updated_settings
    ) as mock_load_settings:
        report = service.set_value(
            "model",
            "gemini-2.5-pro",
        )

    repository.set.assert_called_once_with(
        "model",
        "gemini-2.5-pro",
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
        service.set_value("timeout", "abc")

    repository.set.assert_not_called()


def test_set_value_normalizes_input() -> None:
    settings = create_settings(provider="gemini")

    repository = Mock(spec=ConfigRepository)
    service = ConfigService(settings, repository)

    with patch("diffsage.services.config_service.load_settings", return_value=settings):
        service.set_value("provider", " GEMINI ")
        service.set_value("log_level", " debug ")

    assert repository.set.call_args_list == [
        (("provider", "gemini"),),
        (("log_level", "DEBUG"),),
    ]


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


def test_set_value_reports_config_that_is_still_invalid_after_write() -> None:
    repository = Mock(spec=ConfigRepository)
    service = ConfigService(create_settings(), repository)

    with (
        patch(
            "diffsage.services.config_service.load_settings",
            side_effect=ConfigError("Invalid configuration in config.toml: network.max_retries"),
        ),
        pytest.raises(ConfigError) as error,
    ):
        service.set_value("timeout", "45")

    repository.set.assert_called_once_with("timeout", 45)
    assert str(error.value) == (
        "Configuration updated, but it is still invalid: "
        "Invalid configuration in config.toml: network.max_retries"
    )


def test_unset_value_reports_config_that_is_still_invalid_after_write() -> None:
    repository = Mock(spec=ConfigRepository)
    service = ConfigService(create_settings(), repository)

    with (
        patch(
            "diffsage.services.config_service.load_settings",
            side_effect=ConfigError("still broken"),
        ),
        pytest.raises(ConfigError, match="^Configuration updated, but it is still invalid: "),
    ):
        service.unset_value("timeout")

    repository.unset.assert_called_once_with("timeout")


@pytest.mark.parametrize(
    ("key", "value", "reason"),
    [
        ("timeout", "0", "greater than or equal to 1"),
        ("timeout", "601", "less than or equal to 600"),
        ("max_retries", "-1", "greater than or equal to 0"),
        ("max_retries", "11", "less than or equal to 10"),
        ("log_level", "LOUD", "'DEBUG', 'INFO', 'WARNING', 'ERROR' or 'CRITICAL'"),
        ("provider", "openai", "Input should be 'gemini'"),
        ("model", "   ", "String should have at least 1 character"),
    ],
)
def test_set_value_rejects_values_outside_the_schema(key, value, reason) -> None:
    repository = Mock(spec=ConfigRepository)
    service = ConfigService(create_settings(), repository)

    with pytest.raises(InvalidConfigurationValueError) as error:
        service.set_value(key, value)

    assert str(error.value).startswith(f"Invalid value '{value.strip()}' for {key}: ")
    assert reason in str(error.value)
    repository.set.assert_not_called()


@pytest.mark.parametrize(
    ("key", "value", "stored"),
    [
        ("timeout", "1", 1),
        ("timeout", "600", 600),
        ("max_retries", "0", 0),
        ("max_retries", "10", 10),
    ],
)
def test_set_value_accepts_range_boundaries(key, value, stored) -> None:
    repository = Mock(spec=ConfigRepository)
    service = ConfigService(create_settings(), repository)

    with patch("diffsage.services.config_service.load_settings", return_value=create_settings()):
        service.set_value(key, value)

    repository.set.assert_called_once_with(key, stored)


def test_set_value_keeps_model_case() -> None:
    """Regression: model IDs were lowercased, but they can be case-sensitive."""

    repository = Mock(spec=ConfigRepository)
    service = ConfigService(create_settings(), repository)

    with patch("diffsage.services.config_service.load_settings", return_value=create_settings()):
        service.set_value("model", "  Gemini-2.5-PRO  ")

    repository.set.assert_called_once_with("model", "Gemini-2.5-PRO")
