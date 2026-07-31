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
