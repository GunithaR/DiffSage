from pydantic import BaseModel


class Settings(BaseModel):
    provider: str
    ai_model: str
    api_key: str
    timeout: int
    max_retries: int
    log_level: str
