from pathlib import Path

from platformdirs import user_config_path


def get_global_config_path() -> Path:
    """Return the global DiffSage configuration file path."""

    return user_config_path("DiffSage") / "config.toml"


def get_local_config_path() -> Path:
    """Return the local repository configuration file path."""

    return Path.cwd() / ".diffsage.toml"


def ensure_global_config_dir() -> None:
    """Create the global configuration directory if it does not exist."""

    get_global_config_path().parent.mkdir(
        parents=True,
        exist_ok=True,
    )