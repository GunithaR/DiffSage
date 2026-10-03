from unittest.mock import patch

from diffsage.exceptions import ConfigError
from diffsage.services.doctor_service import DoctorService
from tests.helpers import create_settings


def test_run_reports_loaded_configuration() -> None:
    settings = create_settings(provider="gemini", timeout=90, max_retries=5)

    with patch("diffsage.services.doctor_service.load_settings", return_value=settings):
        report = DoctorService().run()

    assert report.configuration_loaded is True
    assert report.configuration_error is None
    assert report.timeout == 90
    assert report.max_retries == 5


def test_run_reports_invalid_configuration_with_defaults() -> None:
    with patch(
        "diffsage.services.doctor_service.load_settings",
        side_effect=ConfigError("Invalid configuration in config.toml: network.timeout"),
    ):
        report = DoctorService().run()

    assert report.configuration_loaded is False
    assert report.configuration_error == "Invalid configuration in config.toml: network.timeout"
    assert report.timeout == 30
    assert report.max_retries == 3
