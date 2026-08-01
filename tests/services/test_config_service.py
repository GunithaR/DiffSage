from diffsage.services.config_service import ConfigService
from tests.helpers import create_settings


def test_get_configuration_returns_config_report() -> None:
    settings = create_settings(
        provider="gemini",
        ai_model="gemini-3.5-flash-lite",
        timeout=60,
        max_retries=3,
        log_level="INFO",
    )

    service = ConfigService(settings)
    report = service.get_configuration()

    assert report.provider == settings.provider
    assert report.model == settings.ai_model
    assert report.timeout == settings.timeout
    assert report.max_retries == settings.max_retries
    assert report.log_level == settings.log_level