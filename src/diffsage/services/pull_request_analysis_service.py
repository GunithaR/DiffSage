import re

from diffsage.models.git import PullRequestContext
from diffsage.models.pull_request_analysis import (
    ChangeCategory,
    PullRequestAnalysis,
    RiskLevel,
)

TEST_DIRECTORIES = {"test", "tests", "__tests__", "spec", "specs", "testing"}
# test_x.py, x_test.py, x_test.go, x.test.ts, x.spec.js, XTest.java, XTests.cs, conftest.py
TEST_FILE = re.compile(
    r"^(test_.+|.+_test\.[^.]+|.+\.(test|spec)\.[^.]+|.+Tests?\.(java|kt|cs|swift)|conftest\.py)$"
)
AUTHENTICATION_WORDS = {
    "auth",
    "authn",
    "authz",
    "authentication",
    "authorization",
    "authorisation",
    "oauth",
    "oauth2",
    "oidc",
    "sso",
    "login",
    "credential",
    "credentials",
    "password",
    "passwords",
    "security",
    "permission",
    "permissions",
}


def _segments(file: str) -> list[str]:
    """Directory and file names of a path, lowercased."""

    return file.lower().split("/")


def _words(file: str) -> set[str]:
    """Whole words in a path: split on / . _ - and camelCase, lowercased.

    Matching words instead of substrings keeps AUTHORS or author_profile.py from
    counting as authentication.
    """

    spaced = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", file)
    return {word for word in re.split(r"[^A-Za-z0-9]+", spaced.lower()) if word}


class PullRequestAnalysisService:
    def _is_documentation_file(self, file: str) -> bool:
        path = file.lower()

        return "docs" in _segments(file)[:-1] or path.endswith((".md", ".rst", ".adoc"))

    def _is_test_file(self, file: str) -> bool:
        segments = file.split("/")

        return bool(TEST_DIRECTORIES & {part.lower() for part in segments[:-1]}) or bool(
            TEST_FILE.match(segments[-1])
        )

    def _is_dependency_file(self, file: str) -> bool:
        filename = file.rsplit("/", 1)[-1]

        return filename in {
            "pyproject.toml",
            "requirements.txt",
            "requirements-dev.txt",
            "poetry.lock",
            "uv.lock",
            "Pipfile",
            "Pipfile.lock",
            "package.json",
            "package-lock.json",
            "yarn.lock",
            "pnpm-lock.yaml",
            "pom.xml",
            "build.gradle",
            "build.gradle.kts",
            "go.mod",
            "go.sum",
            "Cargo.toml",
            "Cargo.lock",
        }

    def _is_provider_file(self, file: str) -> bool:
        path = file.lower()

        return any(
            part in path.split("/")
            for part in {
                "providers",
                "provider",
                "integrations",
                "integration",
                "adapters",
                "adapter",
                "gateways",
                "gateway",
            }
        )

    def _is_configuration_file(self, file: str) -> bool:
        path = file.lower()
        filename = path.rsplit("/", 1)[-1]

        return (
            path.startswith("config/")
            or "/config/" in path
            or filename
            in {
                ".env",
                ".env.example",
                ".env.template",
                "config.yaml",
                "config.yml",
                "config.json",
                "config.toml",
                "settings.yaml",
                "settings.yml",
                "settings.json",
                "settings.toml",
            }
        )

    def _is_authentication_file(self, file: str) -> bool:
        return bool(AUTHENTICATION_WORDS & _words(file))

    def _is_public_interface_file(self, file: str) -> bool:
        """Network APIs other programs call: changes here can break clients."""

        path = file.lower()

        return bool({"api", "routes", "controllers"} & set(_segments(file)[:-1])) or (
            path.endswith(("openapi.yaml", "openapi.yml", "openapi.json", ".graphql", ".proto"))
        )

    def _is_command_line_file(self, file: str) -> bool:
        """Command-line commands and options: user-facing, but rarely a breaking API."""

        return bool({"cli", "commands"} & set(_segments(file)[:-1]))

    def _calculate_risk_level(
        self,
        categories: list[ChangeCategory],
    ) -> RiskLevel:
        if (
            ChangeCategory.AUTHENTICATION in categories
            or ChangeCategory.PUBLIC_INTERFACE in categories
        ):
            return RiskLevel.HIGH

        if (
            ChangeCategory.PROVIDER in categories
            or ChangeCategory.DEPENDENCY in categories
            or ChangeCategory.CONFIGURATION in categories
            or ChangeCategory.COMMAND_LINE in categories
        ):
            return RiskLevel.MEDIUM

        return RiskLevel.LOW

    def _add_unique(self, values: list, value) -> None:
        if value not in values:
            values.append(value)

    def _detect_signals(
        self,
        files: list[str],
    ) -> PullRequestAnalysis:
        analysis = PullRequestAnalysis()

        for file in files:
            if self._is_documentation_file(file):
                self._add_unique(
                    analysis.change_categories,
                    ChangeCategory.DOCUMENTATION,
                )
                self._add_unique(
                    analysis.changed_areas,
                    "documentation",
                )
                self._add_unique(
                    analysis.reviewer_focus,
                    "documentation-related changes",
                )

            if self._is_test_file(file):
                self._add_unique(
                    analysis.change_categories,
                    ChangeCategory.TEST,
                )
                self._add_unique(
                    analysis.changed_areas,
                    "tests",
                )
                self._add_unique(
                    analysis.reviewer_focus,
                    "test coverage and test changes",
                )

            # A test or a document about authentication is not itself risky: only
            # its own category applies.
            if self._is_test_file(file) or self._is_documentation_file(file):
                continue

            if self._is_dependency_file(file):
                self._add_unique(
                    analysis.change_categories,
                    ChangeCategory.DEPENDENCY,
                )
                self._add_unique(
                    analysis.changed_areas,
                    "dependencies",
                )
                self._add_unique(
                    analysis.risk_signals,
                    "dependency files changed",
                )
                self._add_unique(
                    analysis.reviewer_focus,
                    "dependency and package changes",
                )

            if self._is_provider_file(file):
                self._add_unique(
                    analysis.change_categories,
                    ChangeCategory.PROVIDER,
                )
                self._add_unique(
                    analysis.changed_areas,
                    "provider/integration areas",
                )
                self._add_unique(
                    analysis.risk_signals,
                    "provider/integration-related paths changed",
                )
                self._add_unique(
                    analysis.reviewer_focus,
                    "provider and integration changes",
                )

            if self._is_configuration_file(file):
                self._add_unique(
                    analysis.change_categories,
                    ChangeCategory.CONFIGURATION,
                )
                self._add_unique(
                    analysis.changed_areas,
                    "configuration",
                )
                self._add_unique(
                    analysis.risk_signals,
                    "configuration-related paths changed",
                )
                self._add_unique(
                    analysis.reviewer_focus,
                    "configuration and settings",
                )

            if self._is_authentication_file(file):
                self._add_unique(
                    analysis.change_categories,
                    ChangeCategory.AUTHENTICATION,
                )
                self._add_unique(
                    analysis.changed_areas,
                    "authentication/security areas",
                )
                self._add_unique(
                    analysis.risk_signals,
                    "authentication/security-related paths changed",
                )
                self._add_unique(
                    analysis.reviewer_focus,
                    "authentication and security-related changes",
                )

            if self._is_public_interface_file(file):
                self._add_unique(
                    analysis.change_categories,
                    ChangeCategory.PUBLIC_INTERFACE,
                )
                self._add_unique(
                    analysis.changed_areas,
                    "interface-related areas",
                )
                self._add_unique(
                    analysis.risk_signals,
                    "public-interface-related paths changed",
                )
                self._add_unique(
                    analysis.reviewer_focus,
                    "public interface changes",
                )

            if self._is_command_line_file(file):
                self._add_unique(
                    analysis.change_categories,
                    ChangeCategory.COMMAND_LINE,
                )
                self._add_unique(
                    analysis.changed_areas,
                    "command-line interface",
                )
                self._add_unique(
                    analysis.risk_signals,
                    "command-line interface paths changed",
                )
                self._add_unique(
                    analysis.reviewer_focus,
                    "command-line commands, options and output",
                )

        return analysis

    def analyze(
        self,
        context: PullRequestContext,
    ) -> PullRequestAnalysis:
        analysis = self._detect_signals(context.changed_files)

        analysis.risk_level = self._calculate_risk_level(analysis.change_categories)

        return analysis
