from pydantic import BaseModel


class DoctorReport(BaseModel):
    python_version: str
    git_installed: bool
    git_version: str | None
    provider: str
    timeout: int
    max_retries: int
    log_level: str
    virtual_environment: bool
    configuration_loaded: bool
