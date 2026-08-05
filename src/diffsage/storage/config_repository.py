from pathlib import Path

from tomlkit import TOMLDocument, document, parse, table


class ConfigRepository:
    """Persists DiffSage configuration."""

    _PATH_MAP = {
        "provider": ("ai", "provider"),
        "model": ("ai", "model"),
        "timeout": ("network", "timeout"),
        "max_retries": ("network", "max_retries"),
        "log_level": ("logging", "level"),
    }

    def __init__(self, path: Path) -> None:
        self._path = path


    def _load(self) -> TOMLDocument:
        if not self._path.exists():
            return document()

        content = self._path.read_text()
        doc = parse(content)

        return doc
        

    def _save(self, doc: TOMLDocument) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)

        content = doc.as_string()
        self._path.write_text(content)


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