from unittest.mock import patch

import pytest

from diffsage.commands.config import get_config, list_config, set_config, unset_config
from diffsage.exceptions import InvalidConfigurationValueError, UnknownConfigurationKeyError
from diffsage.models.config import ConfigReport, ConfigValueReport
from tests.helpers import create_settings


def test_list_config_command_orchestrates() -> None:
    settings = create_settings(
        provider="gemini",
        ai_model="gemini-3.5-flash-lite",
        timeout=60,
        max_retries=3,
        log_level="INFO",
    )

    report = ConfigReport(
        provider="gemini",
        model="gemini-3.5-flash-lite",
        timeout=60,
        max_retries=3,
        log_level="INFO",
    )

    with (
        patch(
            "diffsage.commands.config.load_settings", 
            return_value=settings
        ) as mock_load_settings,
        patch("diffsage.commands.config.get_local_config_path") as mock_get_path,
        patch("diffsage.commands.config.ConfigRepository") as mock_repository,
        patch("diffsage.commands.config.ConfigService") as mock_config_service,
        patch("diffsage.commands.config.ConfigView") as mock_config_view,
    ):
        repository = mock_repository.return_value
        service = mock_config_service.return_value
        view = mock_config_view.return_value

        service.get_configuration.return_value = report

        list_config()

    mock_load_settings.assert_called_once()
    mock_get_path.assert_called_once()
    mock_repository.assert_called_once_with(mock_get_path.return_value)
    mock_config_service.assert_called_once_with(settings, repository)
    service.get_configuration.assert_called_once()
    view.show_configuration.assert_called_once_with(report)


def test_get_config_command_orchestrates() -> None:
    settings = create_settings(
        provider="gemini",
        ai_model="gemini-3.5-flash-lite",
        timeout=60,
        max_retries=3,
        log_level="INFO",
    )

    report = ConfigValueReport(
        key="provider",
        value=settings.provider,
    )

    with (
        patch(
            "diffsage.commands.config.load_settings",
            return_value=settings,
        ) as mock_load_settings,
        patch("diffsage.commands.config.get_local_config_path") as mock_get_path,
        patch("diffsage.commands.config.ConfigRepository") as mock_repository,
        patch("diffsage.commands.config.ConfigService") as mock_config_service,
        patch("diffsage.commands.config.ConfigView") as mock_config_view,
    ):
        repository = mock_repository.return_value
        service = mock_config_service.return_value
        view = mock_config_view.return_value

        service.get_value.return_value = report

        get_config(report.key)

    mock_load_settings.assert_called_once()
    mock_get_path.assert_called_once()
    mock_repository.assert_called_once_with(mock_get_path.return_value)
    mock_config_service.assert_called_once_with(settings, repository)
    service.get_value.assert_called_once_with("provider")
    view.show_value.assert_called_once_with(report)


def test_set_config_command_orchestrates() -> None:
    settings = create_settings(
        provider="gemini",
        ai_model="gemini-3.5-flash-lite",
    )

    report = ConfigReport(
        provider="openai",
        model="gpt-5",
        timeout=60,
        max_retries=3,
        log_level="INFO",
    )

    with (
        patch(
            "diffsage.commands.config.load_settings",
            return_value=settings,
        ) as mock_load_settings,
        patch("diffsage.commands.config.get_local_config_path") as mock_get_path,
        patch("diffsage.commands.config.ConfigRepository") as mock_repository,
        patch("diffsage.commands.config.ConfigService") as mock_service,
        patch("diffsage.commands.config.ConfigView") as mock_view,
    ):
        repository = mock_repository.return_value
        service = mock_service.return_value
        view = mock_view.return_value

        service.set_value.return_value = report

        set_config(
            "provider",
            "openai",
        )

    mock_load_settings.assert_called_once()
    mock_get_path.assert_called_once()
    mock_repository.assert_called_once_with(mock_get_path.return_value)
    mock_service.assert_called_once_with(settings, repository)

    service.set_value.assert_called_once_with(
        "provider", 
        "openai",
    )

    view.show_success.assert_called_once_with("Configuration updated.")
    view.show_configuration.assert_called_once_with(report)


def test_set_config_command_handles_unknown_key() -> None:
    settings = create_settings(
        provider="gemini",
        ai_model="gemini-3.5-flash-lite",
    )

    with (
        patch(
            "diffsage.commands.config.load_settings",
            return_value=settings,
        ) as mock_load_settings,
        patch("diffsage.commands.config.get_local_config_path") as mock_get_path,
        patch("diffsage.commands.config.ConfigRepository") as mock_repository,
        patch("diffsage.commands.config.ConfigService") as mock_service,
        patch("diffsage.commands.config.ConfigView") as mock_view,
    ):
        repository = mock_repository.return_value
        service = mock_service.return_value
        view = mock_view.return_value

        service.set_value.side_effect = UnknownConfigurationKeyError("invalid")

        with pytest.raises(SystemExit) as exception_info:
            set_config(
                "invalid",
                "value",
            )

    assert exception_info.value.code == 1

    mock_load_settings.assert_called_once()
    mock_get_path.assert_called_once()
    mock_repository.assert_called_once_with(mock_get_path.return_value)
    mock_service.assert_called_once_with(settings, repository)

    service.set_value.assert_called_once_with(
        "invalid", 
        "value",
    )

    view.show_error.assert_called_once_with(str(UnknownConfigurationKeyError("invalid")))
    view.show_success.assert_not_called()
    view.show_configuration.assert_not_called()


def test_set_config_command_handles_invalid_integer() -> None:
    settings = create_settings(
        provider="gemini",
        ai_model="gemini-3.5-flash-lite",
    )

    with (
        patch(
            "diffsage.commands.config.load_settings",
            return_value=settings,
        ) as mock_load_settings,
        patch("diffsage.commands.config.get_local_config_path") as mock_get_path,
        patch("diffsage.commands.config.ConfigRepository") as mock_repository,
        patch("diffsage.commands.config.ConfigService") as mock_service,
        patch("diffsage.commands.config.ConfigView") as mock_view,
    ):
        repository = mock_repository.return_value
        service = mock_service.return_value
        view = mock_view.return_value

        service.set_value.side_effect = InvalidConfigurationValueError("abc")

        with pytest.raises(SystemExit) as exception_info:
            set_config(
                "timeout",
                "abc",
            )

    assert exception_info.value.code == 1

    mock_load_settings.assert_called_once()
    mock_get_path.assert_called_once()
    mock_repository.assert_called_once_with(mock_get_path.return_value)
    mock_service.assert_called_once_with(settings, repository)

    service.set_value.assert_called_once_with(
        "timeout", 
        "abc",
    )

    view.show_error.assert_called_once_with(str(InvalidConfigurationValueError("abc")))
    view.show_success.assert_not_called()
    view.show_configuration.assert_not_called()


def test_set_config_command_handles_unexpected_error() -> None:
    settings = create_settings(
        provider="gemini",
        ai_model="gemini-3.5-flash-lite",
    )

    with (
        patch(
            "diffsage.commands.config.load_settings",
            return_value=settings,
        ) as mock_load_settings,
        patch("diffsage.commands.config.get_local_config_path") as mock_get_path,
        patch("diffsage.commands.config.ConfigRepository") as mock_repository,
        patch("diffsage.commands.config.ConfigService") as mock_service,
        patch("diffsage.commands.config.ConfigView") as mock_view,
    ):
        repository = mock_repository.return_value
        service = mock_service.return_value
        view = mock_view.return_value

        service.set_value.side_effect = RuntimeError("boom")

        with pytest.raises(SystemExit) as exception_info:
            set_config(
                "provider",
                "abc",
            )

    assert exception_info.value.code == 1

    mock_load_settings.assert_called_once()
    mock_get_path.assert_called_once()
    mock_repository.assert_called_once_with(mock_get_path.return_value)
    mock_service.assert_called_once_with(settings, repository)

    service.set_value.assert_called_once_with(
        "provider", 
        "abc",
    )

    view.show_error.assert_called_once_with(
        "An unexpected error occurred. Please check the log file for more details."
    )
    view.show_success.assert_not_called()
    view.show_configuration.assert_not_called()


def test_unset_config_command_orchestrates() -> None:
    settings = create_settings(
        provider="gemini",
        ai_model="gemini-3.5-flash-lite",
    )

    report = ConfigReport(
        provider="gemini",
        model="gemini-3.5-flash-lite",
        timeout=60,
        max_retries=3,
        log_level="INFO",
    )

    with (
        patch(
            "diffsage.commands.config.load_settings",
            return_value=settings,
        ) as mock_load_settings,
        patch("diffsage.commands.config.get_local_config_path") as mock_get_path,
        patch("diffsage.commands.config.ConfigRepository") as mock_repository,
        patch("diffsage.commands.config.ConfigService") as mock_service,
        patch("diffsage.commands.config.ConfigView") as mock_view,
    ):
        repository = mock_repository.return_value
        service = mock_service.return_value
        view = mock_view.return_value

        service.unset_value.return_value = report

        unset_config(
            "model",
        )

    mock_load_settings.assert_called_once()
    mock_get_path.assert_called_once()
    mock_repository.assert_called_once_with(mock_get_path.return_value)
    mock_service.assert_called_once_with(settings, repository)

    service.unset_value.assert_called_once_with(
        "model",
    )

    view.show_success.assert_called_once_with("Configuration deleted.")
    view.show_configuration.assert_called_once_with(report)


def test_unset_config_command_handles_unknown_key() -> None:
    settings = create_settings(
        provider="gemini",
        ai_model="gemini-3.5-flash-lite",
    )

    with (
        patch(
            "diffsage.commands.config.load_settings",
            return_value=settings,
        ) as mock_load_settings,
        patch("diffsage.commands.config.get_local_config_path") as mock_get_path,
        patch("diffsage.commands.config.ConfigRepository") as mock_repository,
        patch("diffsage.commands.config.ConfigService") as mock_service,
        patch("diffsage.commands.config.ConfigView") as mock_view,
    ):
        repository = mock_repository.return_value
        service = mock_service.return_value
        view = mock_view.return_value

        service.unset_value.side_effect = UnknownConfigurationKeyError("invalid")

        with pytest.raises(SystemExit) as exception_info:
            unset_config("invalid")

    assert exception_info.value.code == 1
    
    mock_load_settings.assert_called_once()
    mock_get_path.assert_called_once()
    mock_repository.assert_called_once_with(mock_get_path.return_value)
    mock_service.assert_called_once_with(settings, repository)

    service.unset_value.assert_called_once_with(
        "invalid",
    )

    view.show_error.assert_called_once_with(str(UnknownConfigurationKeyError("invalid")))
    view.show_success.assert_not_called()
    view.show_configuration.assert_not_called()


def test_unset_config_command_handles_unexpected_error() -> None:
    settings = create_settings(
        provider="gemini",
        ai_model="gemini-3.5-flash-lite",
    )

    with (
        patch(
            "diffsage.commands.config.load_settings",
            return_value=settings,
        ) as mock_load_settings,
        patch("diffsage.commands.config.get_local_config_path") as mock_get_path,
        patch("diffsage.commands.config.ConfigRepository") as mock_repository,
        patch("diffsage.commands.config.ConfigService") as mock_service,
        patch("diffsage.commands.config.ConfigView") as mock_view,
    ):
        repository = mock_repository.return_value
        service = mock_service.return_value
        view = mock_view.return_value

        service.unset_value.side_effect = RuntimeError("boom")

        with pytest.raises(SystemExit) as exception_info:
            unset_config(
                "provider",
            )

    assert exception_info.value.code == 1

    mock_load_settings.assert_called_once()
    mock_get_path.assert_called_once()
    mock_repository.assert_called_once_with(mock_get_path.return_value)
    mock_service.assert_called_once_with(settings, repository)

    service.unset_value.assert_called_once_with(
        "provider",
    )

    view.show_error.assert_called_once_with(
        "An unexpected error occurred. Please check the log file for more details."
    )
    view.show_success.assert_not_called()
    view.show_configuration.assert_not_called()