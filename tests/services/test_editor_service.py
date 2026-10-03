import sys

import pytest

from diffsage.exceptions import DiffSageError, EditorError
from diffsage.services.editor_service import EditorService


def test_edit_raises_editor_error_when_editor_is_missing(monkeypatch) -> None:
    monkeypatch.setenv("VISUAL", "diffsage-missing-editor")

    with pytest.raises(EditorError) as error:
        EditorService().edit("feat: add greeting")

    assert str(error.value) == (
        'Unable to launch "diffsage-missing-editor". Check your EDITOR or VISUAL configuration.'
    )
    assert isinstance(error.value, DiffSageError)


def test_edit_returns_text_written_by_editor(tmp_path, monkeypatch) -> None:
    script = tmp_path / "fake_editor.py"
    script.write_text(
        "import sys\n"
        "from pathlib import Path\n"
        "Path(sys.argv[1]).write_text('fix: edited message\\n', encoding='utf-8')\n"
    )
    # shlex.split (POSIX rules) is used on the editor command, so quote both paths and
    # use forward slashes to keep Windows backslashes from being read as escapes.
    python = sys.executable.replace("\\", "/")
    monkeypatch.setenv("VISUAL", f'"{python}" "{script.as_posix()}"')

    assert EditorService().edit("feat: original message") == "fix: edited message"
