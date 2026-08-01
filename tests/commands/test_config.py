from unittest.mock import patch

from diffsage.commands.config import list_config
from diffsage.models.config_report import ConfigReport
from tests.helpers import create_settings


def test_config_command_orchestrate() -> None:
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
        patch("diffsage.commands.config.ConfigService") as mock_config_service,
        patch("diffsage.commands.config.ConfigView") as mock_config_view,
    ):
        service = mock_config_service.return_value
        view = mock_config_view.return_value
        service.get_configuration.return_value = report

        list_config()

    mock_load_settings.assert_called_once()
    mock_config_service.assert_called_once_with(settings)
    service.get_configuration.assert_called_once()
    view.show_configuration.assert_called_once_with(report)
    