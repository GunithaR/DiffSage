from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from diffsage.cli import app
from diffsage.commands.config import (
    _resolve_scope,
    get_config,
    list_config,
    set_config,
    unset_config,
)
from diffsage.config.scope import ConfigScope
from diffsage.exceptions import (
    ConfigError,
    InvalidConfigurationValueError,
    UnknownConfigurationKeyError,
)
from diffsage.models.config import ConfigReport, ConfigValueReport
from tests.helpers import assert_error_shown, create_settings

runner = CliRunner()


def test_resolve_scope_defaults_to_global() -> None:
    scope = _resolve_scope(
        local=False,
        global_=False,
    )

    assert scope is ConfigScope.GLOBAL


def test_resolve_scope_returns_local() -> None:
    scope = _resolve_scope(
        local=True,
        global_=False,
    )

    assert scope is ConfigScope.LOCAL


def test_resolve_scope_returns_global() -> None:
    scope = _resolve_scope(
        local=False,
        global_=True,
    )

    assert scope is ConfigScope.GLOBAL


def test_resolve_scope_rejects_conflicting_flags() -> None:
    with pytest.raises(ConfigError) as exception_info:
        _resolve_scope(
            local=True,
            global_=True,
        )

    assert str(exception_info.value) == "Cannot specify both --local and --global."


def test_list_config_command_defaults_to_resolved_configuration() -> None:
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
        credential_profile="default",
        max_output_tokens=1000,
        timeout=60,
        max_retries=3,
        log_level="INFO",
    )

    with (
        patch(
            "diffsage.commands.config.load_settings", return_value=settings
        ) as mock_load_settings,
        patch("diffsage.commands.config.configuration_sources") as mock_sources,
        patch("diffsage.commands.config.ConfigService") as mock_config_service,
        patch("diffsage.commands.config.ConfigView") as mock_config_view,
    ):
        service = mock_config_service.return_value
        view = mock_config_view.return_value

        service.get_configuration.return_value = report

        list_config(
            local=False,
            global_=False,
        )

    mock_load_settings.assert_called_once()
    mock_config_service.assert_called_once_with(settings)
    service.get_configuration.assert_called_once()
    view.show_sources.assert_called_once_with(mock_sources.return_value)
    view.show_path.assert_not_called()
    view.show_configuration.assert_called_once_with(report)


def test_list_config_command_uses_local_scope() -> None:
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
        credential_profile="default",
        max_output_tokens=1000,
        timeout=60,
        max_retries=3,
        log_level="INFO",
    )

    with (
        patch(
            "diffsage.commands.config.load_settings_or_defaults", return_value=settings
        ) as mock_load_settings,
        patch("diffsage.commands.config.resolve_config_path") as mock_resolve_path,
        patch("diffsage.commands.config.ConfigRepository") as mock_repository,
        patch("diffsage.commands.config.ConfigService") as mock_config_service,
        patch("diffsage.commands.config.ConfigView") as mock_config_view,
    ):
        repository = mock_repository.return_value
        service = mock_config_service.return_value
        view = mock_config_view.return_value

        service.get_configuration_raw.return_value = report

        list_config(
            local=True,
            global_=False,
        )

    mock_load_settings.assert_called_once()
    mock_resolve_path.assert_called_once_with(ConfigScope.LOCAL)
    mock_repository.assert_called_once_with(mock_resolve_path.return_value)
    mock_config_service.assert_called_once_with(settings, repository)
    service.get_configuration_raw.assert_called_once()
    view.show_path.assert_called_once_with(mock_resolve_path.return_value)
    view.show_configuration.assert_called_once_with(report)


def test_list_config_command_uses_global_scope() -> None:
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
        credential_profile="default",
        max_output_tokens=1000,
        timeout=60,
        max_retries=3,
        log_level="INFO",
    )

    with (
        patch(
            "diffsage.commands.config.load_settings_or_defaults", return_value=settings
        ) as mock_load_settings,
        patch("diffsage.commands.config.resolve_config_path") as mock_resolve_path,
        patch("diffsage.commands.config.ConfigRepository") as mock_repository,
        patch("diffsage.commands.config.ConfigService") as mock_config_service,
        patch("diffsage.commands.config.ConfigView") as mock_config_view,
    ):
        repository = mock_repository.return_value
        service = mock_config_service.return_value
        view = mock_config_view.return_value

        service.get_configuration_raw.return_value = report

        list_config(
            local=False,
            global_=True,
        )

    mock_load_settings.assert_called_once()
    mock_resolve_path.assert_called_once_with(ConfigScope.GLOBAL)
    mock_repository.assert_called_once_with(mock_resolve_path.return_value)
    mock_config_service.assert_called_once_with(settings, repository)
    service.get_configuration_raw.assert_called_once()
    view.show_path.assert_called_once_with(mock_resolve_path.return_value)
    view.show_configuration.assert_called_once_with(report)


def test_get_config_command_defaults_to_resolved_configuration() -> None:
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
        patch("diffsage.commands.config.configuration_sources") as mock_sources,
        patch("diffsage.commands.config.ConfigService") as mock_config_service,
        patch("diffsage.commands.config.ConfigView") as mock_config_view,
    ):
        service = mock_config_service.return_value
        view = mock_config_view.return_value

        service.get_value.return_value = report

        get_config(
            report.key,
            local=False,
            global_=False,
        )

    mock_load_settings.assert_called_once()
    mock_config_service.assert_called_once_with(settings)
    service.get_value.assert_called_once_with("provider")
    view.show_sources.assert_called_once_with(mock_sources.return_value)
    view.show_path.assert_not_called()
    view.show_value.assert_called_once_with(report)


def test_get_config_command_uses_local_scope() -> None:
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
            "diffsage.commands.config.load_settings_or_defaults",
            return_value=settings,
        ) as mock_load_settings,
        patch("diffsage.commands.config.resolve_config_path") as mock_resolve_path,
        patch("diffsage.commands.config.ConfigRepository") as mock_repository,
        patch("diffsage.commands.config.ConfigService") as mock_config_service,
        patch("diffsage.commands.config.ConfigView") as mock_config_view,
    ):
        repository = mock_repository.return_value
        service = mock_config_service.return_value
        view = mock_config_view.return_value

        service.get_configuration_value_raw.return_value = report

        get_config(
            report.key,
            local=True,
            global_=False,
        )

    mock_load_settings.assert_called_once()
    mock_resolve_path.assert_called_once_with(ConfigScope.LOCAL)
    mock_repository.assert_called_once_with(mock_resolve_path.return_value)
    mock_config_service.assert_called_once_with(settings, repository)
    service.get_configuration_value_raw.assert_called_once_with("provider")
    view.show_path.assert_called_once_with(mock_resolve_path.return_value)
    view.show_value.assert_called_once_with(report)


def test_get_config_command_uses_global_scope() -> None:
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
            "diffsage.commands.config.load_settings_or_defaults",
            return_value=settings,
        ) as mock_load_settings,
        patch("diffsage.commands.config.resolve_config_path") as mock_resolve_path,
        patch("diffsage.commands.config.ConfigRepository") as mock_repository,
        patch("diffsage.commands.config.ConfigService") as mock_config_service,
        patch("diffsage.commands.config.ConfigView") as mock_config_view,
    ):
        repository = mock_repository.return_value
        service = mock_config_service.return_value
        view = mock_config_view.return_value

        service.get_configuration_value_raw.return_value = report

        get_config(
            report.key,
            local=False,
            global_=True,
        )

    mock_load_settings.assert_called_once()
    mock_resolve_path.assert_called_once_with(ConfigScope.GLOBAL)
    mock_repository.assert_called_once_with(mock_resolve_path.return_value)
    mock_config_service.assert_called_once_with(settings, repository)
    service.get_configuration_value_raw.assert_called_once_with("provider")
    view.show_path.assert_called_once_with(mock_resolve_path.return_value)
    view.show_value.assert_called_once_with(report)


def test_get_config_rejects_missing_key() -> None:
    result = runner.invoke(app, ["config", "get"])

    assert result.exit_code != 0
    assert "Missing argument" in result.output
    assert "key" in result.output


def test_set_config_command_defaults_to_global() -> None:
    settings = create_settings(
        provider="gemini",
        ai_model="gemini-3.5-flash-lite",
    )

    report = ConfigReport(
        provider="openai",
        model="gpt-5",
        credential_profile="default",
        max_output_tokens=1000,
        timeout=60,
        max_retries=3,
        log_level="INFO",
    )

    with (
        patch(
            "diffsage.commands.config.load_settings_or_defaults",
            return_value=settings,
        ) as mock_load_settings,
        patch("diffsage.commands.config.resolve_config_path") as mock_resolve_path,
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
            local=False,
            global_=False,
        )

    mock_load_settings.assert_called_once()
    mock_resolve_path.assert_called_once_with(ConfigScope.GLOBAL)
    mock_repository.assert_called_once_with(mock_resolve_path.return_value)
    mock_service.assert_called_once_with(settings, repository)

    service.set_value.assert_called_once_with(
        "provider",
        "openai",
    )

    view.show_success.assert_called_once_with("Global configuration updated.")
    view.show_path.assert_called_once_with(
        mock_resolve_path.return_value,
    )
    view.show_configuration.assert_called_once_with(report)


def test_set_config_command_uses_local_scope() -> None:
    settings = create_settings(
        provider="gemini",
        ai_model="gemini-3.5-flash-lite",
    )

    report = ConfigReport(
        provider="openai",
        model="gpt-5",
        credential_profile="default",
        max_output_tokens=1000,
        timeout=60,
        max_retries=3,
        log_level="INFO",
    )

    with (
        patch(
            "diffsage.commands.config.load_settings_or_defaults",
            return_value=settings,
        ) as mock_load_settings,
        patch("diffsage.commands.config.resolve_config_path") as mock_resolve_path,
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
            local=True,
            global_=False,
        )

    mock_load_settings.assert_called_once()
    mock_resolve_path.assert_called_once_with(ConfigScope.LOCAL)
    mock_repository.assert_called_once_with(mock_resolve_path.return_value)
    mock_service.assert_called_once_with(settings, repository)

    service.set_value.assert_called_once_with(
        "provider",
        "openai",
    )

    view.show_success.assert_called_once_with("Local configuration updated.")
    view.show_path.assert_called_once_with(
        mock_resolve_path.return_value,
    )
    view.show_configuration.assert_called_once_with(report)


def test_set_config_command_uses_global_scope() -> None:
    settings = create_settings(
        provider="gemini",
        ai_model="gemini-3.5-flash-lite",
    )

    report = ConfigReport(
        provider="openai",
        model="gpt-5",
        credential_profile="default",
        max_output_tokens=1000,
        timeout=60,
        max_retries=3,
        log_level="INFO",
    )

    with (
        patch(
            "diffsage.commands.config.load_settings_or_defaults",
            return_value=settings,
        ) as mock_load_settings,
        patch("diffsage.commands.config.resolve_config_path") as mock_resolve_path,
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
            local=False,
            global_=True,
        )

    mock_load_settings.assert_called_once()
    mock_resolve_path.assert_called_once_with(ConfigScope.GLOBAL)
    mock_repository.assert_called_once_with(mock_resolve_path.return_value)
    mock_service.assert_called_once_with(settings, repository)

    service.set_value.assert_called_once_with(
        "provider",
        "openai",
    )

    view.show_success.assert_called_once_with("Global configuration updated.")
    view.show_path.assert_called_once_with(
        mock_resolve_path.return_value,
    )
    view.show_configuration.assert_called_once_with(report)


def test_set_config_command_handles_unknown_key(capsys) -> None:
    settings = create_settings(
        provider="gemini",
        ai_model="gemini-3.5-flash-lite",
    )

    with (
        patch(
            "diffsage.commands.config.load_settings_or_defaults",
            return_value=settings,
        ) as mock_load_settings,
        patch("diffsage.commands.config.resolve_config_path") as mock_resolve_path,
        patch("diffsage.commands.config.ConfigRepository") as mock_repository,
        patch("diffsage.commands.config.ConfigService") as mock_service,
        patch("diffsage.commands.config.ConfigView") as mock_view,
    ):
        repository = mock_repository.return_value
        service = mock_service.return_value
        view = mock_view.return_value

        service.set_value.side_effect = UnknownConfigurationKeyError("invalid")

        with pytest.raises(SystemExit) as exception_info:
            set_config("invalid", "value", local=False, global_=True)

    assert exception_info.value.code == 1

    mock_load_settings.assert_called_once()
    mock_resolve_path.assert_called_once_with(ConfigScope.GLOBAL)
    mock_repository.assert_called_once_with(mock_resolve_path.return_value)
    mock_service.assert_called_once_with(settings, repository)

    service.set_value.assert_called_once_with(
        "invalid",
        "value",
    )

    assert_error_shown(capsys, str(UnknownConfigurationKeyError("invalid")))
    view.show_success.assert_not_called()
    view.show_configuration.assert_not_called()


def test_set_config_command_handles_invalid_integer(capsys) -> None:
    settings = create_settings(
        provider="gemini",
        ai_model="gemini-3.5-flash-lite",
    )

    with (
        patch(
            "diffsage.commands.config.load_settings_or_defaults",
            return_value=settings,
        ) as mock_load_settings,
        patch("diffsage.commands.config.resolve_config_path") as mock_resolve_path,
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
                local=False,
                global_=True,
            )

    assert exception_info.value.code == 1

    mock_load_settings.assert_called_once()
    mock_resolve_path.assert_called_once_with(ConfigScope.GLOBAL)
    mock_repository.assert_called_once_with(mock_resolve_path.return_value)
    mock_service.assert_called_once_with(settings, repository)

    service.set_value.assert_called_once_with(
        "timeout",
        "abc",
    )

    assert_error_shown(capsys, str(InvalidConfigurationValueError("abc")))
    view.show_success.assert_not_called()
    view.show_configuration.assert_not_called()


def test_set_config_command_handles_unexpected_error(capsys) -> None:
    settings = create_settings(
        provider="gemini",
        ai_model="gemini-3.5-flash-lite",
    )

    with (
        patch(
            "diffsage.commands.config.load_settings_or_defaults",
            return_value=settings,
        ) as mock_load_settings,
        patch("diffsage.commands.config.resolve_config_path") as mock_resolve_path,
        patch("diffsage.commands.config.ConfigRepository") as mock_repository,
        patch("diffsage.commands.config.ConfigService") as mock_service,
        patch("diffsage.commands.config.ConfigView") as mock_view,
    ):
        repository = mock_repository.return_value
        service = mock_service.return_value
        view = mock_view.return_value

        service.set_value.side_effect = RuntimeError("boom")

        with pytest.raises(SystemExit) as exception_info:
            set_config("provider", "abc", local=False, global_=True)

    assert exception_info.value.code == 1

    mock_load_settings.assert_called_once()
    mock_resolve_path.assert_called_once_with(ConfigScope.GLOBAL)
    mock_repository.assert_called_once_with(mock_resolve_path.return_value)
    mock_service.assert_called_once_with(settings, repository)

    service.set_value.assert_called_once_with(
        "provider",
        "abc",
    )

    assert_error_shown(
        capsys, "An unexpected error occurred. Please check the log file for more details."
    )
    view.show_success.assert_not_called()
    view.show_configuration.assert_not_called()


def test_set_config_rejects_missing_key() -> None:
    result = runner.invoke(app, ["config", "set"])

    assert result.exit_code != 0
    assert "Missing argument" in result.output
    assert "key" in result.output


def test_unset_config_command_defaults_to_global() -> None:
    settings = create_settings(
        provider="gemini",
        ai_model="gemini-3.5-flash-lite",
    )

    report = ConfigReport(
        provider="gemini",
        model="gemini-3.5-flash-lite",
        credential_profile="default",
        max_output_tokens=1000,
        timeout=60,
        max_retries=3,
        log_level="INFO",
    )

    with (
        patch(
            "diffsage.commands.config.load_settings_or_defaults",
            return_value=settings,
        ) as mock_load_settings,
        patch("diffsage.commands.config.resolve_config_path") as mock_resolve_path,
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
            local=False,
            global_=False,
        )

    mock_load_settings.assert_called_once()
    mock_resolve_path.assert_called_once_with(ConfigScope.GLOBAL)
    mock_repository.assert_called_once_with(mock_resolve_path.return_value)
    mock_service.assert_called_once_with(settings, repository)

    service.unset_value.assert_called_once_with(
        "model",
    )

    view.show_success.assert_called_once_with("Global configuration removed.")
    view.show_path.assert_called_once_with(
        mock_resolve_path.return_value,
    )
    view.show_configuration.assert_called_once_with(report)


def test_unset_config_command_uses_local_scope() -> None:
    settings = create_settings(
        provider="gemini",
        ai_model="gemini-3.5-flash-lite",
    )

    report = ConfigReport(
        provider="gemini",
        model="gemini-3.5-flash-lite",
        credential_profile="default",
        max_output_tokens=1000,
        timeout=60,
        max_retries=3,
        log_level="INFO",
    )

    with (
        patch(
            "diffsage.commands.config.load_settings_or_defaults",
            return_value=settings,
        ) as mock_load_settings,
        patch("diffsage.commands.config.resolve_config_path") as mock_resolve_path,
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
            local=True,
            global_=False,
        )

    mock_load_settings.assert_called_once()
    mock_resolve_path.assert_called_once_with(ConfigScope.LOCAL)
    mock_repository.assert_called_once_with(mock_resolve_path.return_value)
    mock_service.assert_called_once_with(settings, repository)

    service.unset_value.assert_called_once_with(
        "model",
    )

    view.show_success.assert_called_once_with("Local configuration removed.")
    view.show_path.assert_called_once_with(
        mock_resolve_path.return_value,
    )
    view.show_configuration.assert_called_once_with(report)


def test_unset_config_command_uses_global_scope() -> None:
    settings = create_settings(
        provider="gemini",
        ai_model="gemini-3.5-flash-lite",
    )

    report = ConfigReport(
        provider="gemini",
        model="gemini-3.5-flash-lite",
        credential_profile="default",
        max_output_tokens=1000,
        timeout=60,
        max_retries=3,
        log_level="INFO",
    )

    with (
        patch(
            "diffsage.commands.config.load_settings_or_defaults",
            return_value=settings,
        ) as mock_load_settings,
        patch("diffsage.commands.config.resolve_config_path") as mock_resolve_path,
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
            local=False,
            global_=True,
        )

    mock_load_settings.assert_called_once()
    mock_resolve_path.assert_called_once_with(ConfigScope.GLOBAL)
    mock_repository.assert_called_once_with(mock_resolve_path.return_value)
    mock_service.assert_called_once_with(settings, repository)

    service.unset_value.assert_called_once_with(
        "model",
    )

    view.show_success.assert_called_once_with("Global configuration removed.")
    view.show_path.assert_called_once_with(
        mock_resolve_path.return_value,
    )
    view.show_configuration.assert_called_once_with(report)


def test_unset_config_command_handles_unknown_key(capsys) -> None:
    settings = create_settings(
        provider="gemini",
        ai_model="gemini-3.5-flash-lite",
    )

    with (
        patch(
            "diffsage.commands.config.load_settings_or_defaults",
            return_value=settings,
        ) as mock_load_settings,
        patch("diffsage.commands.config.resolve_config_path") as mock_resolve_path,
        patch("diffsage.commands.config.ConfigRepository") as mock_repository,
        patch("diffsage.commands.config.ConfigService") as mock_service,
        patch("diffsage.commands.config.ConfigView") as mock_view,
    ):
        repository = mock_repository.return_value
        service = mock_service.return_value
        view = mock_view.return_value

        service.unset_value.side_effect = UnknownConfigurationKeyError("invalid")

        with pytest.raises(SystemExit) as exception_info:
            unset_config(
                "invalid",
                local=False,
                global_=True,
            )

    assert exception_info.value.code == 1

    mock_load_settings.assert_called_once()
    mock_resolve_path.assert_called_once_with(ConfigScope.GLOBAL)
    mock_repository.assert_called_once_with(mock_resolve_path.return_value)
    mock_service.assert_called_once_with(settings, repository)

    service.unset_value.assert_called_once_with(
        "invalid",
    )

    assert_error_shown(capsys, str(UnknownConfigurationKeyError("invalid")))
    view.show_success.assert_not_called()
    view.show_configuration.assert_not_called()


def test_unset_config_command_handles_unexpected_error(capsys) -> None:
    settings = create_settings(
        provider="gemini",
        ai_model="gemini-3.5-flash-lite",
    )

    with (
        patch(
            "diffsage.commands.config.load_settings_or_defaults",
            return_value=settings,
        ) as mock_load_settings,
        patch("diffsage.commands.config.resolve_config_path") as mock_resolve_path,
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
                local=False,
                global_=True,
            )

    assert exception_info.value.code == 1

    mock_load_settings.assert_called_once()
    mock_resolve_path.assert_called_once_with(ConfigScope.GLOBAL)
    mock_repository.assert_called_once_with(mock_resolve_path.return_value)
    mock_service.assert_called_once_with(settings, repository)

    service.unset_value.assert_called_once_with(
        "provider",
    )

    assert_error_shown(
        capsys, "An unexpected error occurred. Please check the log file for more details."
    )
    view.show_success.assert_not_called()
    view.show_configuration.assert_not_called()


def test_unset_config_rejects_missing_key() -> None:
    result = runner.invoke(app, ["config", "unset"])

    assert result.exit_code != 0
    assert "Missing argument" in result.output
    assert "key" in result.output
