import json
import os
import subprocess
import sys
from pathlib import Path

from diffsage.models.provider import ProviderRequest, ProviderResponse
from diffsage.providers.base import BaseProvider

FAKE_GH_SCRIPT = Path(__file__).with_name("fake_gh.py")


class FakeProvider(BaseProvider):
    """AI provider that returns queued responses and records every request."""

    def __init__(self) -> None:
        self._responses: list[str | BaseException] = []
        self.requests: list[ProviderRequest] = []

    def queue(self, *responses: str | BaseException) -> None:
        """Queue response texts, or exceptions to raise, in call order."""

        self._responses.extend(responses)

    @property
    def prompts(self) -> list[str]:
        return [request.prompt for request in self.requests]

    def generate(self, request: ProviderRequest) -> ProviderResponse:
        self.requests.append(request)

        if not self._responses:
            raise AssertionError("FakeProvider received a request with no queued response.")

        response = self._responses.pop(0)

        if isinstance(response, BaseException):
            raise response

        return ProviderResponse(
            content=response,
            provider="fake",
            model=request.model,
            input_tokens=0,
            output_tokens=0,
            finish_reason="STOP",
            latency_ms=0,
        )


class FakeGitHubCLI:
    """Controls the fake `gh` executable and records its invocations."""

    def __init__(self, state_path: Path) -> None:
        self._state_path = state_path
        self.installed = True

        self._save(
            {
                "authenticated": True,
                "pr_url": "https://github.com/example/repo/pull/1",
                "pr_create_error": None,
                "calls": [],
            }
        )

    def _load(self) -> dict:
        return json.loads(self._state_path.read_text(encoding="utf-8"))

    def _save(self, state: dict) -> None:
        self._state_path.write_text(json.dumps(state), encoding="utf-8")

    def configure(self, **changes: object) -> None:
        """Change fake behaviour: authenticated, pr_url or pr_create_error."""

        state = self._load()
        state.update(changes)
        self._save(state)

    @property
    def calls(self) -> list[list[str]]:
        return self._load()["calls"]

    def run(self, args: list[str]) -> subprocess.CompletedProcess[str]:
        """Run the fake CLI the same way GitHubClient runs the real one."""

        if not self.installed:
            raise FileNotFoundError("gh")

        return subprocess.run(
            [sys.executable, str(FAKE_GH_SCRIPT), *args],
            env={**os.environ, "FAKE_GH_STATE": str(self._state_path)},
            capture_output=True,
            text=True,
            check=True,
        )
