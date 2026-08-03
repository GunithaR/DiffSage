from pathlib import Path

from tomlkit import document, parse, table

from diffsage.storage.config_repository import ConfigRepository


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