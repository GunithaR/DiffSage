import pytest

from diffsage.services.diff_sanitizer import REDACTED, sanitize


def file_diff(path: str, *added: str) -> str:
    lines = [
        f"diff --git a/{path} b/{path}",
        f"--- a/{path}",
        f"+++ b/{path}",
        f"@@ -0,0 +1,{len(added)} @@",
        *(f"+{line}" for line in added),
    ]
    return "\n".join(lines)


def added_lines(text: str) -> list[str]:
    return [
        line[1:]
        for line in text.splitlines()
        if line.startswith("+") and not line.startswith("+++")
    ]


@pytest.mark.parametrize(
    "secret",
    [
        "AIzaSyA1234567890abcdefghijklmnopqrstuv",
        "ghp_" + "a" * 36,
        "github_pat_" + "B" * 30,
        "AKIAABCDEFGHIJKLMNOP",
        "xoxb-1234567890-abcdefghij",
        "sk-abcdefghijklmnopqrstuvwxyz",
        "sk-ant-abcdefghijklmnopqrstuvwxyz",
        "sk-proj-abcdefghijklmnopqrstuvwxyz",
    ],
)
def test_known_token_formats_are_redacted_anywhere_in_a_line(secret) -> None:
    result = sanitize(file_diff("app.py", f"client = Client(key={secret!r})"))

    assert secret not in result.text
    assert added_lines(result.text) == [f"client = Client(key='{REDACTED}')"]
    assert result.redactions == 1


@pytest.mark.parametrize(
    ("line", "expected"),
    [
        ('api_key = "hunter2-hunter2"', f'api_key = "{REDACTED}"'),
        ("PASSWORD: 'correct-horse'", f"PASSWORD: '{REDACTED}'"),
        ('{"client_secret": "s3cr3t-value"}', f'{{"client_secret": "{REDACTED}"}}'),
        ("STRIPE_SECRET=sk_live_abcdefgh", f"STRIPE_SECRET={REDACTED}"),
        ("export DB_PASSWORD=supersecret1", f"export DB_PASSWORD={REDACTED}"),
    ],
)
def test_credential_assignments_with_literal_values_are_redacted(line, expected) -> None:
    result = sanitize(file_diff("config.py", line))

    assert added_lines(result.text) == [expected]
    assert result.redactions == 1


@pytest.mark.parametrize(
    "line",
    [
        "password = read_password()",
        'DB_PASSWORD = os.environ["DB_PASSWORD"]',
        "API_TOKEN=${API_TOKEN}",
        'token = get_token("x")',
        'api_key = ""',
        "timeout = 30",
        "def rotate_secret(self):",
    ],
)
def test_code_that_only_mentions_secrets_is_left_alone(line) -> None:
    """Regression: an early version redacted function calls and environment lookups."""

    result = sanitize(file_diff("app.py", line))

    assert added_lines(result.text) == [line]
    assert result.redactions == 0


def test_private_key_block_is_collapsed_to_one_line() -> None:
    result = sanitize(
        file_diff(
            "deploy/key.txt",
            "-----BEGIN OPENSSH PRIVATE KEY-----",
            "b3BlbnNzaC1rZXktdjEAAAAABG5vbmUAAAAEbm9uZQ",
            "-----END OPENSSH PRIVATE KEY-----",
            "after the key",
        )
    )

    assert added_lines(result.text) == ["[REDACTED PRIVATE KEY]", "after the key"]
    assert "b3BlbnNz" not in result.text
    assert result.redactions == 1


def test_removed_and_context_lines_are_redacted_too() -> None:
    diff = "\n".join(
        [
            "diff --git a/a.py b/a.py",
            "--- a/a.py",
            "+++ b/a.py",
            "@@ -1,2 +1,2 @@",
            ' token = "old-token-value"',
            '-api_key = "removed-key-value"',
            '+api_key = "new-key-value-1"',
        ]
    )

    result = sanitize(diff)

    assert "old-token-value" not in result.text
    assert "removed-key-value" not in result.text
    assert "new-key-value-1" not in result.text
    assert result.redactions == 3


@pytest.mark.parametrize(
    "path", [".env", "config/.env.production", "certs/server.pem", "id_ed25519", "deploy/app.key"]
)
def test_secret_bearing_files_have_their_contents_omitted(path) -> None:
    result = sanitize(file_diff(path, "ANYTHING=at-all"))

    assert result.text.splitlines() == [
        f"diff --git a/{path} b/{path}",
        "[contents omitted: file may contain secrets]",
    ]
    assert result.secret_files == [path]


def test_env_templates_are_sent_with_values_redacted() -> None:
    result = sanitize(file_diff(".env.example", "API_TOKEN=replace-me-please", "DEBUG=true"))

    assert result.secret_files == []
    assert added_lines(result.text) == [f"API_TOKEN={REDACTED}", "DEBUG=true"]


@pytest.mark.parametrize("path", ["package-lock.json", "web/yarn.lock", "uv.lock", "go.sum"])
def test_lockfiles_have_their_contents_omitted(path) -> None:
    result = sanitize(file_diff(path, '"version": "2"'))

    assert result.text.splitlines()[1] == "[contents omitted: lockfile]"
    assert result.lockfiles == [path]


def test_binary_and_ordinary_changes_pass_through_unchanged() -> None:
    diff = "\n".join(
        [
            "diff --git a/logo.png b/logo.png",
            "Binary files a/logo.png and b/logo.png differ",
            file_diff("src/app.py", "print('hello')"),
        ]
    )

    result = sanitize(diff)

    assert result.text == diff
    assert result.notices() == []


def test_diff_over_the_limit_keeps_whole_files_in_order_and_lists_the_rest() -> None:
    first = file_diff("a.py", "x" * 60)
    second = file_diff("b.py", "y" * 60)
    third = file_diff("c.py", "z" * 60)

    result = sanitize("\n".join([first, second, third]), max_characters=len(first) + 20)

    assert result.text == first
    assert result.truncated_files == ["b.py", "c.py"]
    assert "2 file(s) were left out: b.py, c.py" in result.notices()[0]


def test_single_file_over_the_limit_is_cut_short_with_a_marker() -> None:
    result = sanitize(file_diff("big.py", "x" * 500), max_characters=200)

    assert len(result.text) < 300
    assert result.text.endswith("[diff truncated: file too large]")
    assert result.shortened_file == "big.py"


def test_notices_describe_every_change() -> None:
    diff = "\n".join(
        [
            file_diff("app.py", 'api_key = "hunter2-hunter2"'),
            file_diff(".env", "A=b"),
            file_diff("poetry.lock", "x"),
        ]
    )

    notices = sanitize(diff).notices()

    assert notices == [
        f"1 value(s) that looked like secrets were replaced with {REDACTED}.",
        "Contents of files that may hold secrets were not sent: .env",
        "Lockfile contents were not sent: poetry.lock",
    ]


def test_empty_diff_stays_empty() -> None:
    result = sanitize("")

    assert result.text == ""
    assert result.notices() == []
