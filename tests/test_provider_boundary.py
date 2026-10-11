"""The provider interface stays free of provider-specific types, so a new provider
(for example a local Ollama model) only needs code inside diffsage/providers/."""

import ast
import subprocess
import sys
from pathlib import Path

import pytest
from typer.testing import CliRunner

import diffsage
from diffsage.cli import app
from diffsage.providers.factory import PROVIDERS
from tests.fakes import FakeProvider

SOURCE = Path(diffsage.__file__).parent
PROVIDERS_PACKAGE = SOURCE / "providers"

runner = CliRunner()


def imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    modules = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)

    return modules


def test_only_the_providers_package_imports_a_provider_sdk() -> None:
    offenders = {
        str(path.relative_to(SOURCE)): sorted(
            module for module in imported_modules(path) if module.split(".")[0] == "google"
        )
        for path in SOURCE.rglob("*.py")
        if not path.is_relative_to(PROVIDERS_PACKAGE)
    }

    assert {path: modules for path, modules in offenders.items() if modules} == {}


def test_starting_the_cli_does_not_load_the_gemini_sdk() -> None:
    """Regression: every command spent about a third of a second importing the Gemini
    SDK, even commands such as `config list` that never call the AI."""

    code = "import sys, diffsage.cli; print('google.genai' in sys.modules)"
    result = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True, check=True
    )

    assert result.stdout.strip() == "False"


@pytest.fixture
def local_provider(monkeypatch) -> FakeProvider:
    """A provider added the way a real one would be: one entry in PROVIDERS."""

    provider = FakeProvider()
    monkeypatch.setitem(PROVIDERS, "local", lambda _settings, _credential: provider)

    return provider


def test_a_provider_registered_only_in_the_factory_works_end_to_end(
    local_provider, monkeypatch
) -> None:
    monkeypatch.setenv("DIFFSAGE_API_KEY", "local-key")
    local_provider.queue("Hello from the local model.")

    configured = runner.invoke(app, ["config", "set", "provider", "local", "--global"])
    answered = runner.invoke(app, ["ask", "hi"])

    assert configured.exit_code == 0, configured.output
    assert answered.exit_code == 0, answered.output
    assert "Hello from the local model." in answered.output
    assert local_provider.prompts == ["hi"]


@pytest.mark.usefixtures("local_provider")
def test_unknown_provider_lists_every_registered_provider() -> None:
    result = runner.invoke(app, ["config", "set", "provider", "openai", "--global"])

    assert result.exit_code == 1
    assert "Input should be 'gemini' or 'local'" in " ".join(result.output.split())
