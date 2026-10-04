import os
import platform
import shlex
import subprocess
import tempfile
from pathlib import Path

from diffsage.exceptions import EditorError


class EditorService:
    def edit(self, text: str) -> str:
        editor = self._resolve_editor()

        temp_file = self._create_temp_file(text)

        command = shlex.split(editor)
        command.append(str(temp_file))

        try:
            subprocess.run(command, check=False)
            text = temp_file.read_text(encoding="utf-8")
            return text.rstrip()

        except FileNotFoundError as e:
            raise EditorError(
                f'Unable to launch "{editor}". Check your EDITOR or VISUAL configuration.'
            ) from e

        finally:
            temp_file.unlink(missing_ok=True)

    def _resolve_editor(self) -> str:
        editor = os.environ.get("VISUAL")
        if editor:
            return editor

        editor = os.environ.get("EDITOR")
        if editor:
            return editor

        try:
            result = subprocess.run(
                [
                    "git",
                    "config",
                    "--global",
                    "core.editor",
                ],
                capture_output=True,
                text=True,
                check=True,
            )
            editor = result.stdout.strip()
            if editor:
                return editor

        except (subprocess.CalledProcessError, FileNotFoundError):
            pass

        if platform.system() == "Windows":
            return "notepad"

        return "nano"

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
