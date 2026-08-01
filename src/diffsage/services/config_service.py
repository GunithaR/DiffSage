from diffsage.config.settings import Settings
from diffsage.exceptions import UnknownConfigurationKeyError
from diffsage.models.config import ConfigReport, ConfigValueReport


class ConfigService:
    _KEY_MAP = {
        "provider": "provider",
        "model": "ai_model",
        "timeout": "timeout",
        "max_retries": "max_retries",
        "log_level": "log_level",
    }

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

    def get_value(self, key: str) -> ConfigValueReport:
        attribute = self._KEY_MAP.get(key)

        if attribute is None:
            raise UnknownConfigurationKeyError(key)

        value = getattr(self._settings, attribute)

        return ConfigValueReport(
            key=key,
            value=str(value)
        )