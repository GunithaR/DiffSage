import subprocess
from pathlib import Path

from platformdirs import user_config_path, user_log_path

from diffsage.git.client import GitClient

APP_NAME = "DiffSage"


def get_global_config_path() -> Path:
    """Return the global DiffSage configuration file path."""

    return user_config_path("DiffSage") / "config.toml"


def display_path(path: Path) -> str:
    """Show a path with the home directory shortened to '~'."""

    home = Path.home()

    if path.is_relative_to(home):
        return str(Path("~") / path.relative_to(home))

    return str(path)


def find_repository_root() -> Path | None:
    """Return the root of the Git working tree containing the current directory.

    Git is asked directly, because in worktrees and submodules `.git` is a file rather
    than a directory. Returns None outside a working tree or if Git is not installed.
    """

    try:
        return GitClient().repository_root()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


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
