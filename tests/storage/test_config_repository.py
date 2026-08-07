from pathlib import Path

from tomlkit import document, parse, table

from diffsage.storage.config_repository import ConfigRepository


def test_list_returns_all_configured_values(tmp_path: Path) -> None:
    path = tmp_path / ".diffsage.toml"

    doc = document()
    doc["ai"] = table()
    doc["ai"]["provider"] = "gemini"
    doc["ai"]["model"] = "gemini-3.5-flash-lite"

    doc["network"] = table()
    doc["network"]["timeout"] = 30
    doc["network"]["max_retries"] = 3

    doc["logging"] = table()
    doc["logging"]["level"] = "INFO"

    path.write_text(doc.as_string())

    repository = ConfigRepository(path)
    repo_list = repository.list()

    assert repo_list["provider"] == "gemini"
    assert repo_list["model"] == "gemini-3.5-flash-lite"
    assert repo_list["timeout"] == 30
    assert repo_list["max_retries"] == 3
    assert repo_list["log_level"] == "INFO"


def test_list_ignores_missing_values(tmp_path: Path) -> None:
    path = tmp_path / ".diffsage.toml"

    doc = document()
    doc["ai"] = table()
    doc["ai"]["provider"] = "gemini"

    path.write_text(doc.as_string())

    repository = ConfigRepository(path)
    repo_list = repository.list()

    assert "provider" in repo_list
    assert repo_list["provider"] == "gemini"
    assert "model" not in repo_list
    assert "timeout" not in repo_list
    assert "max_retries" not in repo_list
    assert "log_level" not in repo_list


def test_list_returns_empty_configuration(tmp_path: Path) -> None:
    path = tmp_path / ".diffsage.toml"

    doc = document()
    path.write_text(doc.as_string())

    repository = ConfigRepository(path)
    repo_list = repository.list()

    assert repo_list == {}


def test_list_returns_configuration_keys(tmp_path: Path) -> None:
    path = tmp_path / ".diffsage.toml"

    doc = document()
    doc["ai"] = table()
    doc["ai"]["provider"] = "gemini"

    doc["logging"] = table()
    doc["logging"]["level"] = "INFO"

    path.write_text(doc.as_string())

    repository = ConfigRepository(path)
    repo_list = repository.list()

    assert "provider" in repo_list
    assert "log_level" in repo_list
    assert "ai" not in repo_list
    assert "logging" not in repo_list


def test_get_returns_existing_value(tmp_path: Path) -> None:
    path = tmp_path / ".diffsage.toml"

    doc = document()
    doc["ai"] = table()
    doc["ai"]["provider"] = "gemini"

    doc["network"] = table()
    doc["network"]["timeout"] = 30

    path.write_text(doc.as_string())

    repository = ConfigRepository(path)

    assert repository.get("provider") == "gemini"
    assert repository.get("timeout") == 30


def test_get_returns_none_for_missing_value(tmp_path: Path) -> None:
    path = tmp_path / ".diffsage.toml"
    
    doc = document()
    doc["ai"] = table()
    doc["ai"]["provider"] = "gemini"

    path.write_text(doc.as_string())

    repository = ConfigRepository(path)

    assert repository.get("timeout") is None


def test_get_returns_none_for_empty_configuration(tmp_path: Path) -> None:
    path = tmp_path / ".diffsage.toml"
    
    doc = document()
    path.write_text(doc.as_string())

    repository = ConfigRepository(path)

    assert repository.get("provider") is None


def test_set_updates_existing_value(tmp_path: Path) -> None:
    path = tmp_path / ".diffsage.toml"

    doc = document()
    doc["ai"] = table()
    doc["ai"]["provider"] = "gemini"

    path.write_text(doc.as_string())

    repository = ConfigRepository(path)
    repository.set("provider", "openai")

    updated = parse(path.read_text())

    assert updated["ai"]["provider"] == "openai"


def test_set_creates_missing_table(tmp_path: Path) -> None:
    path = tmp_path / ".diffsage.toml"

    doc = document()
    path.write_text(doc.as_string())

    repository = ConfigRepository(path)
    repository.set("provider", "gemini")

    updated = parse(path.read_text())

    assert "ai" in updated
    assert updated["ai"]["provider"] == "gemini"


def test_set_preserves_existing_configuration(tmp_path: Path) -> None:
    path = tmp_path / ".diffsage.toml"
    
    doc = document()
    doc["ai"] = table()
    doc["ai"]["provider"] = "gemini"

    path.write_text(doc.as_string())

    repository = ConfigRepository(path)
    repository.set("log_level", "INFO")

    updated = parse(path.read_text())

    assert updated["ai"]["provider"] == "gemini"
    assert "logging" in updated 
    assert updated["logging"]["level"] == "INFO"


def test_set_creates_parent_directory(tmp_path: Path) -> None:
    path = tmp_path / "config" / ".diffsage.toml"

    assert not path.parent.exists()

    repository = ConfigRepository(path)
    repository.set("provider", "gemini")

    updated = parse(path.read_text())

    assert path.parent.exists()
    assert path.exists()
    assert updated["ai"]["provider"] == "gemini"


def test_unset_removes_existing_key(tmp_path: Path) -> None:
    path = tmp_path / ".diffsage.toml"

    doc = document()
    doc["ai"] = table()
    doc["ai"]["provider"] = "gemini"
    doc["ai"]["model"] = "gemini-3.5-flash-lite"

    path.write_text(doc.as_string())

    repository = ConfigRepository(path)
    repository.unset("provider")

    updated = parse(path.read_text())

    assert "provider" not in updated["ai"]
    assert updated["ai"]["model"] == "gemini-3.5-flash-lite"


def test_unset_removes_empty_section(tmp_path: Path) -> None:
    path = tmp_path / ".diffsage.toml"

    doc = document()
    doc["ai"] = table()
    doc["ai"]["provider"] = "gemini"

    path.write_text(doc.as_string())

    repository = ConfigRepository(path)
    repository.unset("provider")

    updated = parse(path.read_text())

    assert "ai" not in updated


def test_unset_preserves_existing_configuration(tmp_path: Path) -> None:
    path = tmp_path / ".diffsage.toml"
    
    doc = document()
    doc["ai"] = table()
    doc["ai"]["provider"] = "gemini"
    doc["ai"]["model"] = "gemini-3.5-flash-lite"

    doc["logging"] = table()
    doc["logging"]["level"] = "INFO"

    path.write_text(doc.as_string())

    repository = ConfigRepository(path)
    repository.unset("provider")

    updated = parse(path.read_text())

    assert "provider" not in updated["ai"]
    assert updated["ai"]["model"] == "gemini-3.5-flash-lite"
    assert updated["logging"]["level"] == "INFO"


def test_unset_missing_key_is_noop(tmp_path: Path) -> None:
    path = tmp_path / ".diffsage.toml"

    doc = document()
    doc["ai"] = table()
    doc["ai"]["provider"] = "gemini"
    path.write_text(doc.as_string())

    repository = ConfigRepository(path)

    before = path.read_text()

    repository.unset("model")

    after = path.read_text()

    updated = parse(path.read_text())

    assert updated["ai"]["provider"] == "gemini"
    assert "model" not in updated["ai"]
    assert before == after