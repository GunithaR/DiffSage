from pydantic import ValidationError

from diffsage.config.loader import load_settings
from diffsage.config.schema import CONFIG_KEYS, PartialDiffSageConfig
from diffsage.config.settings import Settings
from diffsage.exceptions import (
    ConfigError,
    InvalidConfigurationValueError,
    UnknownConfigurationKeyError,
)
from diffsage.models.config import ConfigReport, ConfigValueReport, RawConfigReport
from diffsage.storage.config_repository import ConfigRepository


class ConfigService:
    _ATTRIBUTE_MAP = {
        "provider": "provider",
        "model": "ai_model",
        "credential_profile": "credential_profile",
        "max_output_tokens": "max_output_tokens",
        "timeout": "timeout",
        "max_retries": "max_retries",
        "log_level": "log_level",
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
            credential_profile=settings.credential_profile,
            max_output_tokens=settings.max_output_tokens,
            timeout=settings.timeout,
            max_retries=settings.max_retries,
            log_level=settings.log_level,
        )

    def get_configuration_raw(self) -> RawConfigReport:
        config = self._file.list()

        return RawConfigReport(
            provider=config.get("provider"),
            model=config.get("model"),
            credential_profile=config.get("credential_profile"),
            max_output_tokens=config.get("max_output_tokens"),
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
        if key not in CONFIG_KEYS:
            raise UnknownConfigurationKeyError(key)

        # Case is left alone: the schema normalises provider and log_level, and model IDs
        # can be case-sensitive.
        value = value.strip()
        validated = self._validate(key, value)

        self._file.set(key, validated)

        return self._reload_report()

    @staticmethod
    def _validate(key: str, value: str) -> str | int:
        """Check a value against the configuration schema and return it converted."""

        section, option = CONFIG_KEYS[key]

        try:
            partial = PartialDiffSageConfig.model_validate({section: {option: value}})
        except ValidationError as error:
            reason = "; ".join(detail["msg"] for detail in error.errors())
            raise InvalidConfigurationValueError(value, key=key, reason=reason) from None

        return getattr(getattr(partial, section), option)

    def unset_value(self, key: str) -> ConfigReport:
        attribute_name = self._ATTRIBUTE_MAP.get(key)

        if attribute_name is None:
            raise UnknownConfigurationKeyError(key)

        self._file.unset(key)

        return self._reload_report()
