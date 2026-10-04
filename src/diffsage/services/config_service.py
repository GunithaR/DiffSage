from diffsage.config.loader import load_settings
from diffsage.config.settings import Settings
from diffsage.exceptions import (
    ConfigError,
    InvalidConfigurationValueError,
    UnknownConfigurationKeyError,
)
from diffsage.models.config import ConfigReport, ConfigValueReport
from diffsage.storage.config_repository import ConfigRepository


class ConfigService:
    _ATTRIBUTE_MAP = {
        "provider": "provider",
        "model": "ai_model",
        "timeout": "timeout",
        "max_retries": "max_retries",
        "log_level": "log_level",
    }

    _NORMALIZERS = {
        "provider": str.lower,
        "model": str.lower,
        "log_level": str.upper,
    }

    def __init__(self, settings: Settings, repository: ConfigRepository | None = None) -> None:
        self._settings = settings
        self._repository = repository

    @property
    def _file(self) -> ConfigRepository:
        """The configuration file this service reads and writes.

        Only file operations need it; the resolved views work from settings alone.
        """

        if self._repository is None:
            raise RuntimeError("ConfigService was created without a configuration file.")

        return self._repository

    def _reload_report(self) -> ConfigReport:
        """Report the configuration after a write; the write itself has already succeeded."""

        try:
            updated_settings = load_settings()
        except ConfigError as error:
            raise ConfigError(
                f"Configuration updated, but it is still invalid: {error.message}"
            ) from error

        return self._create_report(updated_settings)

    def _create_report(self, settings: Settings) -> ConfigReport:
        return ConfigReport(
            provider=settings.provider,
            model=settings.ai_model,
            timeout=settings.timeout,
            max_retries=settings.max_retries,
            log_level=settings.log_level,
        )

    def get_configuration_raw(self) -> ConfigReport:
        config = self._file.list()

        return ConfigReport(
            provider=config.get("provider"),
            model=config.get("model"),
            timeout=config.get("timeout"),
            max_retries=config.get("max_retries"),
            log_level=config.get("log_level"),
        )

    def get_configuration_value_raw(self, key: str) -> ConfigValueReport:
        if key not in self._ATTRIBUTE_MAP:
            raise UnknownConfigurationKeyError(key)

        value = self._file.get(key)

        return ConfigValueReport(
            key=key,
            value=value,
        )

    def get_configuration(self) -> ConfigReport:
        return self._create_report(self._settings)

    def get_value(self, key: str) -> ConfigValueReport:
        current_value = self._ATTRIBUTE_MAP.get(key)

        if current_value is None:
            raise UnknownConfigurationKeyError(key)

        value = getattr(self._settings, current_value)

        return ConfigValueReport(key=key, value=str(value))

    def set_value(self, key: str, value: str) -> ConfigReport:
        attribute_name = self._ATTRIBUTE_MAP.get(key)

        if attribute_name is None:
            raise UnknownConfigurationKeyError(key)

        value = value.strip()
        normalizer = self._NORMALIZERS.get(key)

        if normalizer is not None:
            value = normalizer(value)

        expected_value = getattr(self._settings, attribute_name)

        try:
            if isinstance(expected_value, int):
                converted_value = int(value)
            else:
                converted_value = value
        except ValueError:
            raise InvalidConfigurationValueError(value) from None

        self._file.set(key, converted_value)

        return self._reload_report()

    def unset_value(self, key: str) -> ConfigReport:
        attribute_name = self._ATTRIBUTE_MAP.get(key)

        if attribute_name is None:
            raise UnknownConfigurationKeyError(key)

        self._file.unset(key)

        return self._reload_report()
