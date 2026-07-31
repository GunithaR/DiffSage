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


class PartialAIConfig(BaseModel):
    provider: str | None = None
    model: str | None = None


class PartialNetworkConfig(BaseModel):
    timeout: int | None = None
    max_retries: int | None = None


class PartialLoggingConfig(BaseModel):
    level: str | None = None


class PartialDiffSageConfig(BaseModel):
    ai: PartialAIConfig | None = None
    network: PartialNetworkConfig | None = None
    logging: PartialLoggingConfig | None = None