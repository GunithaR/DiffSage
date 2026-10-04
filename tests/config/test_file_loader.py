from pathlib import Path

import pytest

from diffsage.config.file_loader import load_config
from diffsage.config.paths import display_path
from diffsage.exceptions import ConfigError


def write_config(tmp_path: Path, content: str) -> Path:
    path = tmp_path / "config.toml"
    path.write_text(content)
    return path


def test_load_config_reads_valid_values(tmp_path) -> None:
    path = write_config(tmp_path, '[ai]\nmodel = "gemini-pro"\n\n[network]\ntimeout = 45\n')

    config = load_config(path)

    assert config.ai.model == "gemini-pro"
    assert config.network.timeout == 45
    assert config.logging is None


def test_load_config_reports_missing_file(tmp_path) -> None:
    with pytest.raises(ConfigError, match="Configuration file not found"):
        load_config(tmp_path / "missing.toml")


def test_load_config_reports_toml_syntax_error_with_position(tmp_path) -> None:
    path = write_config(tmp_path, "[network\ntimeout = 5\n")

    with pytest.raises(ConfigError) as error:
        load_config(path)

    message = str(error.value)
    assert message.startswith(f"Invalid TOML syntax in {display_path(path)}:")
    assert "line 1" in message


def test_load_config_reports_each_invalid_value(tmp_path) -> None:
    path = write_config(tmp_path, '[network]\ntimeout = "abc"\nmax_retries = "x"\n')

    with pytest.raises(ConfigError) as error:
        load_config(path)

    message = str(error.value)
    assert message.startswith(f"Invalid configuration in {display_path(path)}:")
    assert "network.timeout: Input should be a valid integer" in message
    assert "(got 'abc')" in message
    assert "network.max_retries" in message
    assert "(got 'x')" in message


def test_load_config_reports_wrong_section_type(tmp_path) -> None:
    path = write_config(tmp_path, 'network = "fast"\n')

    with pytest.raises(ConfigError, match=r"network: .*\(got 'fast'\)"):
        load_config(path)


def test_load_config_shortens_home_directory(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    write_config(tmp_path, '[network]\ntimeout = "abc"\n')

    with pytest.raises(ConfigError) as error:
        load_config(tmp_path / "config.toml")

    assert str(error.value).startswith(f"Invalid configuration in {Path('~') / 'config.toml'}:")
