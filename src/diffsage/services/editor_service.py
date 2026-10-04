import os
import platform
import shlex
import subprocess
import tempfile
from pathlib import Path

from diffsage.exceptions import EditorError


class EditorService:
    def edit(self, text: str) -> str | None:
        """Open `text` in the user's editor and return the saved text.

        Returns None when the edit is cancelled: the editor exited with a non-zero status
        (for example `:cq` in vim), or the text was saved empty. That matches `git commit`,
        which also aborts on an empty message.
        """

        editor = self._resolve_editor()
        temp_file = self._create_temp_file(text)

        command = shlex.split(editor)
        command.append(str(temp_file))

        try:
            result = subprocess.run(command, check=False)

            if result.returncode != 0:
                return None

            edited = temp_file.read_text(encoding="utf-8").rstrip()
            return edited if edited.strip() else None

        except FileNotFoundError as e:
            raise EditorError(
                f'Unable to launch "{editor}". Check core.editor, or the GIT_EDITOR, VISUAL '
                "or EDITOR environment variables."
            ) from e

        finally:
            temp_file.unlink(missing_ok=True)

    def _resolve_editor(self) -> str:
        """Use the same editor as `git commit`.

        `git var GIT_EDITOR` applies Git's own order: GIT_EDITOR, core.editor (any config
        level), VISUAL (only when TERM is not "dumb"), EDITOR, then Git's default. Without
        Git, fall back to VISUAL, EDITOR, then a platform default.
        """

        try:
            result = subprocess.run(
                ["git", "var", "GIT_EDITOR"],
                capture_output=True,
                text=True,
                check=True,
            )
            editor = result.stdout.strip()

            if editor:
                return editor

        except (subprocess.CalledProcessError, FileNotFoundError):
            pass

        for variable in ("VISUAL", "EDITOR"):
            editor = os.environ.get(variable, "").strip()

            if editor:
                return editor

        return "notepad" if platform.system() == "Windows" else "nano"

    def _create_temp_file(self, text: str) -> Path:
        with tempfile.NamedTemporaryFile(
            delete=False,
            mode="w",
            encoding="utf-8",
            suffix=".txt",
        ) as temp:
            temp.write(text)
            temp.flush()
            path = Path(temp.name)

        return path
