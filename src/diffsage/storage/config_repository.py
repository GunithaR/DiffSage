from pathlib import Path

from tomlkit import TOMLDocument, document, parse, table
from tomlkit.exceptions import ParseError

from diffsage.config.paths import display_path
from diffsage.config.schema import CONFIG_KEYS
from diffsage.exceptions import ConfigError


class ConfigRepository:
    """Persists DiffSage configuration."""

    _PATH_MAP = CONFIG_KEYS

    def __init__(self, path: Path) -> None:
        self._path = path

    def _load(self) -> TOMLDocument:
        if not self._path.exists():
            return document()

        content = self._path.read_text()

        try:
            return parse(content)
        except ParseError as error:
            raise ConfigError(
                f"Invalid TOML syntax in {display_path(self._path)}: {error}. "
                "DiffSage cannot edit a file it cannot parse; fix that line in a text editor."
            ) from error

    def _save(self, doc: TOMLDocument) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)

        content = doc.as_string()
        self._path.write_text(content)

    def list(self) -> dict[str, str | int]:
        doc = self._load()

        config = {}

        for key, (section, option) in self._PATH_MAP.items():
            if section in doc and option in doc[section]:
                config[key] = doc[section][option]

        return config

    def get(self, key: str) -> str | int | None:
        doc = self._load()

        section, option = self._PATH_MAP[key]

        if section not in doc:
            return None

        if option not in doc[section]:
            return None

        return doc[section][option]

    def set(self, key: str, value: str | int) -> None:
        doc = self._load()
        section, option = self._PATH_MAP[key]

        if section not in doc:
            doc[section] = table()

        doc[section][option] = value

        self._save(doc)

    def unset(self, key: str) -> None:
        doc = self._load()
        section, option = self._PATH_MAP[key]

        if section not in doc:
            return

        if option not in doc[section]:
            return

        del doc[section][option]

        if not doc[section]:
            del doc[section]

        self._save(doc)
