"""Process exit codes: a stable contract for scripts, git hooks and CI.

Each code stands for one kind of problem, so a caller can react without parsing the
message. Codes are only ever added, never renumbered. Documented in the README under
"Exit Codes"; a test keeps that table in step with this list.
"""

from enum import IntEnum


class ExitCode(IntEnum):
    OK = 0
    ERROR = 1
    USAGE = 2
    CONFIGURATION = 3
    CREDENTIALS = 4
    GIT = 5
    AI_PROVIDER = 6
    AI_OUTPUT = 7
    GITHUB = 8
    INTERRUPTED = 130
