import pytest


@pytest.fixture
def clean_diffsage_env(monkeypatch):
    variables = [
        "DIFFSAGE_PROVIDER",
        "DIFFSAGE_AI_MODEL",
        "DIFFSAGE_TIMEOUT",
        "DIFFSAGE_MAX_RETRIES",
        "DIFFSAGE_LOG_LEVEL",
    ]

    for variable in variables:
        monkeypatch.delenv(variable, raising=False)
