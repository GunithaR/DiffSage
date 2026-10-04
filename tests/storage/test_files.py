import os
import stat
from pathlib import Path
from unittest.mock import patch

import pytest

from diffsage.storage.files import restrict_to_owner, write_private_text

posix_only = pytest.mark.skipif(os.name != "posix", reason="Unix permission bits only")


def mode(path: Path) -> int:
    return stat.S_IMODE(path.stat().st_mode)


@posix_only
def test_write_private_text_creates_owner_only_file(tmp_path) -> None:
    path = tmp_path / "nested" / "secret.toml"

    write_private_text(path, "api_key = 'x'\n")

    assert path.read_text() == "api_key = 'x'\n"
    assert mode(path) == 0o600


@posix_only
def test_write_private_text_tightens_an_existing_world_readable_file(tmp_path) -> None:
    path = tmp_path / "secret.toml"
    path.write_text("old")
    os.chmod(path, 0o644)

    write_private_text(path, "new")

    assert path.read_text() == "new"
    assert mode(path) == 0o600


def test_failed_write_keeps_the_old_file_and_leaves_no_temporary_file(tmp_path) -> None:
    folder = tmp_path / "credentials"
    folder.mkdir()
    path = folder / "secret.toml"
    path.write_text("original")

    with (
        patch("diffsage.storage.files.os.replace", side_effect=OSError("disk full")),
        pytest.raises(OSError, match="disk full"),
    ):
        write_private_text(path, "replacement")

    assert path.read_text() == "original"
    assert sorted(p.name for p in folder.iterdir()) == ["secret.toml"]


@posix_only
@pytest.mark.parametrize(("before", "after"), [(0o644, 0o600), (0o666, 0o600), (0o600, 0o600)])
def test_restrict_to_owner_removes_group_and_other_access(tmp_path, before, after) -> None:
    path = tmp_path / "secret.toml"
    path.write_text("x")
    os.chmod(path, before)

    restrict_to_owner(path)

    assert mode(path) == after
