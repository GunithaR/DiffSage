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
        credential_profile="default",
        max_output_tokens=1000,
    ),
    network=NetworkConfig(
        timeout=30,
        max_retries=3,
    ),
    logging=LoggingConfig(
        level="INFO",
    ),
)
