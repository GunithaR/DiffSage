from pydantic import BaseModel


class AIConfig(BaseModel):
    provider: str
    model: str


class NetworkConfig(BaseModel):
    timeout: int
    max_retries: int


class LoggingConfig(BaseModel):
    level: str


# Reserved for future multi-provider support.
#
# class ProviderCredentials(BaseModel):
#     api_key: str | None = None
#
#
# class ProvidersConfig(BaseModel):
#     gemini: ProviderCredentials
#     openai: ProviderCredentials
#     anthropic: ProviderCredentials


class DiffSageConfig(BaseModel):
    ai: AIConfig
    network: NetworkConfig
    logging: LoggingConfig