from pathlib import Path

from platformdirs import user_config_path, user_log_path

APP_NAME = "DiffSage"

def get_global_config_path() -> Path:
    """Return the global DiffSage configuration file path."""

    return user_config_path("DiffSage") / "config.toml"


def find_repository_root() -> Path | None:
    """Return the Git repository root or None if not inside a repository."""
    current = Path.cwd()

    while True:
        if (current / ".git").is_dir():
            return current

        if current.parent == current:
            return None

        current = current.parent


def get_local_config_path() -> Path | None:
    """Return the local repository configuration file path."""

    root = find_repository_root()

    if root is None:
        return None
    
    return root / ".diffsage.toml"


def get_log_directory() -> Path:
    path = user_log_path(APP_NAME)
    path.mkdir(parents=True, exist_ok=True)
    return path

def get_log_file_path() -> Path:
    return get_log_directory() / "diffsage.log"

def ensure_global_config_dir() -> None:
    """Create the global configuration directory if it does not exist."""

    get_global_config_path().parent.mkdir(
        parents=True,
        exist_ok=True,
    )

def get_credentials_path() -> Path:
    """Return the global DiffSage credentials file path."""

    return user_config_path(APP_NAME) / "credentials.toml"