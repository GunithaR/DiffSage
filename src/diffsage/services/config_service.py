from diffsage.config.settings import Settings
from diffsage.models.config_report import ConfigReport


class ConfigService:

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def get_configuration(self) -> ConfigReport:

        return ConfigReport(
            provider=self._settings.provider,
            model=self._settings.ai_model,
            timeout=self._settings.timeout,
            max_retries=self._settings.max_retries,
            log_level=self._settings.log_level,
        )

