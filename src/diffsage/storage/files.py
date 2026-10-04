"""File helpers for data that must stay private to the current user."""

import os
import stat
import tempfile
from pathlib import Path

OWNER_ONLY = 0o600


def restrict_to_owner(path: Path) -> None:
    """Remove group and other permissions from an existing file.

    Unix permission bits do not exist on Windows; there the file lives under the user's
    own profile folder, which Windows already restricts to that user.
    """

    if os.name != "posix":
        return

    if stat.S_IMODE(path.stat().st_mode) & 0o077:
        os.chmod(path, OWNER_ONLY)


def write_private_text(path: Path, content: str) -> None:
    """Atomically write text to a file readable and writable only by the current user.

    The content goes to a temporary file in the same folder first, which is then renamed
    over the target, so a crash or a full disk can never leave a half-written file.
    """

    path.parent.mkdir(parents=True, exist_ok=True)

    # mkstemp creates the file with mode 0600 on POSIX.
    descriptor, temporary_name = tempfile.mkstemp(
        dir=path.parent, prefix=f".{path.name}.", suffix=".tmp"
    )
    temporary = Path(temporary_name)

    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as file:
            file.write(content)
            file.flush()
            os.fsync(file.fileno())

        os.replace(temporary, path)

    except BaseException:
        temporary.unlink(missing_ok=True)
        raise

    restrict_to_owner(path)
