from pydantic import BaseModel

from diffsage.config.defaults import (
    DEFAULT_LOG_LEVEL,
    DEFAULT_API_KEY,
    DEFAULT_MAX_RETRIES,
    DEFAULT_PROVIDER,
    DEFAULT_TIMEOUT,
)

class Settings(BaseModel):
    provider: str = DEFAULT_PROVIDER
    api_key: str = DEFAULT_API_KEY
    timeout: int = DEFAULT_TIMEOUT
    max_retries: int = DEFAULT_MAX_RETRIES
    log_level: str = DEFAULT_LOG_LEVEL
