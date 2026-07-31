DEFAULT_PROVIDER = "gemini"
DEFAULT_AI_MODEL = "gemini-3.5-flash-lite"
DEFAULT_API_KEY = ""
DEFAULT_TIMEOUT = 30
DEFAULT_MAX_RETRIES = 3
DEFAULT_LOG_LEVEL = "INFO"

from diffsage.config.schema import (
    AIConfig,
    DiffSageConfig,
    LoggingConfig,
    NetworkConfig,
)

DEFAULT_CONFIG = DiffSageConfig(
    ai=AIConfig(
        provider="gemini",
        model="gemini-3.5-flash-lite",
    ),
    network=NetworkConfig(
        timeout=30,
        max_retries=3,
    ),
    logging=LoggingConfig(
        level="INFO",
    ),
)
