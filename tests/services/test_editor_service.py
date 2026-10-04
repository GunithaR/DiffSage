import platform
import sys

import pytest

from diffsage.exceptions import DiffSageError, EditorError
from diffsage.services.editor_service import EditorService
from tests.helpers import run_git


def test_edit_raises_editor_error_when_editor_is_missing(monkeypatch) -> None:
    monkeypatch.setenv("GIT_EDITOR", "diffsage-missing-editor")

    with pytest.raises(EditorError) as error:
        EditorService().edit("feat: add greeting")

    assert str(error.value) == (
        'Unable to launch "diffsage-missing-editor". Check core.editor, or the GIT_EDITOR, VISUAL '
        "or EDITOR environment variables."
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
    monkeypatch.setenv("GIT_EDITOR", f'"{python}" "{script.as_posix()}"')

    assert EditorService().edit("feat: original message") == "fix: edited message"


def python_editor(tmp_path, monkeypatch, code: str) -> None:
    """Set GIT_EDITOR to a Python script; argv[1] is the file being edited."""

    script = tmp_path / "editor.py"
    script.write_text(code)
    python = sys.executable.replace("\\", "/")
    monkeypatch.setenv("GIT_EDITOR", f'"{python}" "{script.as_posix()}"')


def test_non_zero_editor_exit_cancels_the_edit(tmp_path, monkeypatch) -> None:
    """Regression: the exit code was ignored, so aborting vim (:cq) still used the file."""

    python_editor(
        tmp_path,
        monkeypatch,
        "import sys\nfrom pathlib import Path\n"
        "Path(sys.argv[1]).write_text('fix: half-typed')\nsys.exit(1)\n",
    )

    assert EditorService().edit("feat: original") is None


@pytest.mark.parametrize("saved", ["", "   \n\n  "])
def test_saving_an_empty_message_cancels_the_edit(tmp_path, monkeypatch, saved) -> None:
    python_editor(
        tmp_path,
        monkeypatch,
        f"import sys\nfrom pathlib import Path\nPath(sys.argv[1]).write_text({saved!r})\n",
    )

    assert EditorService().edit("feat: original") is None


def test_editor_is_chosen_the_way_git_chooses_it(git_repo, monkeypatch) -> None:
    """Regression: VISUAL/EDITOR were used even when core.editor said otherwise, so DiffSage
    and `git commit` opened different editors."""

    run_git(["config", "core.editor", "repo-editor --wait"], git_repo)
    monkeypatch.setenv("TERM", "xterm")
    monkeypatch.setenv("VISUAL", "visual-editor")
    monkeypatch.setenv("EDITOR", "plain-editor")

    assert EditorService()._resolve_editor() == "repo-editor --wait"

    monkeypatch.setenv("GIT_EDITOR", "git-editor")

    assert EditorService()._resolve_editor() == "git-editor"


@pytest.mark.parametrize(
    ("variables", "expected"),
    [
        ({"VISUAL": "visual-editor", "EDITOR": "plain-editor"}, "visual-editor"),
        ({"EDITOR": "plain-editor"}, "plain-editor"),
        ({}, "notepad" if platform.system() == "Windows" else "nano"),
    ],
)
def test_without_git_the_environment_and_a_platform_default_are_used(
    monkeypatch, variables, expected
) -> None:
    monkeypatch.setenv("PATH", "")

    for name, value in variables.items():
        monkeypatch.setenv(name, value)

    assert EditorService()._resolve_editor() == expected


def test_editor_path_with_non_ascii_characters_is_read_correctly(git_repo) -> None:
    """Git prints UTF-8; on Windows the default code page would garble this path."""

    run_git(["config", "core.editor", "C:/Users/José/editor --wait"], git_repo)

    assert EditorService()._resolve_editor() == "C:/Users/José/editor --wait"
