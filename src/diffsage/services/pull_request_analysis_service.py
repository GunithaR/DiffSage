from diffsage.models.git import PullRequestContext
from diffsage.models.pull_request_analysis import (
    ChangeCategory,
    PullRequestAnalysis,
    RiskLevel,
)


class PullRequestAnalysisService:
    def _is_documentation_file(self, file: str) -> bool:
        return (
            file.startswith("docs/")
            or file == "README.md"
            or file.endswith(".md")
            or file.endswith(".rst")
        )

    def _is_test_file(self, file: str) -> bool:
        return file.startswith("tests/") or file.startswith("test_") or file.endswith("_test.py")

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
        path = file.lower()

        return any(
            keyword in path
            for keyword in {
                "auth",
                "authentication",
                "authorization",
                "credential",
                "credentials",
                "security",
                "permission",
                "permissions",
            }
        )

    def _is_public_interface_file(self, file: str) -> bool:
        path = file.lower()

        return (
            "/api/" in path
            or path.startswith("api/")
            or "/routes/" in path
            or path.startswith("routes/")
            or "/controllers/" in path
            or path.startswith("controllers/")
            or path.endswith("openapi.yaml")
            or path.endswith("openapi.yml")
            or path.endswith("openapi.json")
            or path.endswith("schema.graphql")
            or path.endswith(".graphql")
            or "/cli/" in path
            or path.startswith("cli/")
            or "/commands/" in path
            or path.startswith("commands/")
        )

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

        return analysis

    def analyze(
        self,
        context: PullRequestContext,
    ) -> PullRequestAnalysis:
        analysis = self._detect_signals(context.changed_files)

        analysis.risk_level = self._calculate_risk_level(analysis.change_categories)

        return analysis
