"""Make Git diffs safe and reasonably sized before they are sent to an AI provider.

Per file in a unified diff:
- files that typically hold secrets (.env, private keys, ...) have their contents omitted;
- lockfiles have their contents omitted (large, generated, no value for a summary);
- in every other file, values that look like credentials are replaced with [REDACTED].
Then the whole diff is capped in size, keeping whole files in their original order.
"""

import re
from dataclasses import dataclass, field
from pathlib import PurePosixPath

REDACTED = "[REDACTED]"
MAX_DIFF_CHARACTERS = 100_000

LOCKFILES = {
    "package-lock.json",
    "npm-shrinkwrap.json",
    "yarn.lock",
    "pnpm-lock.yaml",
    "poetry.lock",
    "uv.lock",
    "pipfile.lock",
    "cargo.lock",
    "go.sum",
    "composer.lock",
    "gemfile.lock",
    "packages.lock.json",
}

SECRET_FILE_NAMES = {
    ".env",
    ".npmrc",
    ".pypirc",
    ".netrc",
    "id_rsa",
    "id_dsa",
    "id_ecdsa",
    "id_ed25519",
    "credentials.toml",
}
SECRET_FILE_SUFFIXES = (".pem", ".key", ".p12", ".pfx", ".jks", ".keystore")
# .env variants that conventionally hold placeholders, not real values. Their values
# still go through pattern redaction below.
ENV_TEMPLATES = {".env.example", ".env.sample", ".env.template", ".env.dist"}

# Well-known credential formats: the whole match is a secret.
TOKEN_PATTERNS = [
    re.compile(r"AIza[0-9A-Za-z_\-]{35}"),  # Google API key
    re.compile(r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{36,}\b"),  # GitHub token
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]{22,}\b"),  # GitHub fine-grained token
    re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b"),  # AWS access key ID
    re.compile(r"\bxox[abprs]-[A-Za-z0-9\-]{10,}\b"),  # Slack token
    re.compile(r"\bsk-(?:ant-|proj-)?[A-Za-z0-9_\-]{20,}\b"),  # OpenAI / Anthropic key
]

# key = "value" assignments whose name says it is a credential. Only literal values
# are redacted, so code such as `password = read_password()` is left alone.
_SECRET_NAME = r"[A-Za-z0-9_.\-]*(?:api[_\-]?key|secret|token|passw(?:or)?d|private[_\-]?key)"
QUOTED_ASSIGNMENT = re.compile(
    rf"(?i)(?P<name>{_SECRET_NAME}[A-Za-z0-9_.\-]*\"?\s*[:=]\s*)(?P<quote>[\"'])(?P<value>[^\"'\s]{{8,}})(?P=quote)"
)
# Env-file style NAME=value: uppercase name, no spaces around "=", and a plain value (not
# a variable reference or a call), so code like `PASSWORD = os.environ["X"]` is left alone.
ENV_ASSIGNMENT = re.compile(
    r"^(?P<name>(?:export\s+)?[A-Z0-9_]*(?:API_?KEY|SECRET|TOKEN|PASSWORD|PASSWD|PRIVATE_?KEY)"
    r"[A-Z0-9_]*=)(?P<value>[^\s\"'#$<{%(][^\s()]{7,})$"
)

PRIVATE_KEY_BEGIN = re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")
PRIVATE_KEY_END = re.compile(r"-----END [A-Z ]*PRIVATE KEY-----")

_FILE_HEADER = re.compile(r"^diff --git a/(?P<old>.+) b/(?P<new>.+)$")


@dataclass(slots=True)
class SanitizedDiff:
    """A diff that is safe to send, plus what was changed to make it so."""

    text: str
    redactions: int = 0
    secret_files: list[str] = field(default_factory=list)
    lockfiles: list[str] = field(default_factory=list)
    truncated_files: list[str] = field(default_factory=list)
    shortened_file: str | None = None

    def notices(self) -> list[str]:
        """Plain-language notes, shown to the user and added to the prompt."""

        notes = []

        if self.redactions:
            notes.append(
                f"{self.redactions} value(s) that looked like secrets were replaced with "
                f"{REDACTED}."
            )

        if self.secret_files:
            notes.append(
                "Contents of files that may hold secrets were not sent: "
                + ", ".join(self.secret_files)
            )

        if self.lockfiles:
            notes.append("Lockfile contents were not sent: " + ", ".join(self.lockfiles))

        if self.shortened_file:
            notes.append(f"The diff was too large, so {self.shortened_file} was cut short.")

        if self.truncated_files:
            notes.append(
                f"The diff was too large, so {len(self.truncated_files)} file(s) were left "
                "out: " + ", ".join(self.truncated_files)
            )

        return notes


def _file_path(header: str) -> str:
    match = _FILE_HEADER.match(header)
    return match.group("new") if match else header


def _is_lockfile(path: str) -> bool:
    return PurePosixPath(path).name.lower() in LOCKFILES


def _is_secret_file(path: str) -> bool:
    name = PurePosixPath(path).name.lower()

    if name in ENV_TEMPLATES:
        return False

    return (
        name in SECRET_FILE_NAMES or name.startswith(".env.") or name.endswith(SECRET_FILE_SUFFIXES)
    )


def _split_files(diff: str) -> list[list[str]]:
    """Split a unified diff into per-file line lists (text before the first header is kept)."""

    sections: list[list[str]] = []

    for line in diff.splitlines():
        if line.startswith("diff --git ") or not sections:
            sections.append([line])
        else:
            sections[-1].append(line)

    return sections


def _redact_line(content: str) -> tuple[str, int]:
    """Redact credentials in one line of file content (without its diff prefix)."""

    count = 0

    for pattern in TOKEN_PATTERNS:
        content, found = pattern.subn(REDACTED, content)
        count += found

    def replace_quoted(match: re.Match[str]) -> str:
        nonlocal count

        if match.group("value") == REDACTED:
            return match.group(0)

        count += 1
        return f"{match.group('name')}{match.group('quote')}{REDACTED}{match.group('quote')}"

    content = QUOTED_ASSIGNMENT.sub(replace_quoted, content)

    match = ENV_ASSIGNMENT.match(content)

    if match and match.group("value") != REDACTED:
        content = f"{match.group('name')}{REDACTED}"
        count += 1

    return content, count


def _redact_section(lines: list[str]) -> tuple[list[str], int]:
    """Redact one file's diff, keeping the header and +/-/space prefixes intact."""

    result: list[str] = []
    count = 0
    in_private_key = False
    in_hunk = False

    for line in lines:
        if line.startswith("@@"):
            in_hunk = True
            result.append(line)
            continue

        if not in_hunk or not line or line[0] not in "+- ":
            result.append(line)
            continue

        prefix, content = line[0], line[1:]

        if in_private_key:
            if PRIVATE_KEY_END.search(content):
                in_private_key = False
            continue

        if PRIVATE_KEY_BEGIN.search(content):
            result.append(f"{prefix}[REDACTED PRIVATE KEY]")
            count += 1
            in_private_key = not PRIVATE_KEY_END.search(content)
            continue

        redacted, found = _redact_line(content)
        count += found
        result.append(prefix + redacted)

    return result, count


def sanitize(diff: str, max_characters: int = MAX_DIFF_CHARACTERS) -> SanitizedDiff:
    """Return a version of `diff` that is safe and small enough to send to an AI provider."""

    report = SanitizedDiff(text="")
    kept: list[str] = []
    size = 0

    for section in _split_files(diff):
        header = section[0]
        path = _file_path(header)

        if header.startswith("diff --git ") and _is_secret_file(path):
            section = [header, "[contents omitted: file may contain secrets]"]
            report.secret_files.append(path)
        elif header.startswith("diff --git ") and _is_lockfile(path):
            section = [header, "[contents omitted: lockfile]"]
            report.lockfiles.append(path)
        else:
            section, found = _redact_section(section)
            report.redactions += found

        text = "\n".join(section)

        if kept and size + len(text) > max_characters:
            report.truncated_files.append(path)
            continue

        if len(text) > max_characters:
            text = text[:max_characters] + "\n[diff truncated: file too large]"
            report.shortened_file = path

        kept.append(text)
        size += len(text) + 1

    report.text = "\n".join(kept)
    return report
