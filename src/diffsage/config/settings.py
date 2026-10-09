from pydantic import BaseModel


class Settings(BaseModel):
    provider: str
    ai_model: str
    credential_profile: str
    max_output_tokens: int
    timeout: int
    max_retries: int
    log_level: str
