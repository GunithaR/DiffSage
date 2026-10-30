import pytest

from diffsage.models.git import PullRequestContext
from diffsage.models.pull_request_analysis import (
    ChangeCategory,
    RiskLevel,
)
from diffsage.services.pull_request_analysis_service import PullRequestAnalysisService


def test_analyze_documentation_only_change_returns_low_risk() -> None:
    context = PullRequestContext(
        current_branch="feature/docs",
        base_branch="main",
        merge_base="abc123",
        commits=[],
        changed_files=[
            "README.md",
            "docs/architecture.md",
        ],
        diff="",
    )

    service = PullRequestAnalysisService()
    analysis = service.analyze(context)

    assert analysis.risk_level == RiskLevel.LOW
    assert ChangeCategory.DOCUMENTATION in analysis.change_categories
    assert "documentation" in analysis.changed_areas


def test_analyze_test_only_change_returns_low_risk() -> None:
    context = PullRequestContext(
        current_branch="feature/tests",
        base_branch="main",
        merge_base="abc123",
        commits=[],
        changed_files=[
            "tests/services/test_git_service.py",
            "tests/git/test_client.py",
        ],
        diff="",
    )

    service = PullRequestAnalysisService()
    analysis = service.analyze(context)

    assert analysis.risk_level == RiskLevel.LOW
    assert ChangeCategory.TEST in analysis.change_categories
    assert "tests" in analysis.changed_areas
    assert "test coverage and test changes" in analysis.reviewer_focus


def test_analyze_dependency_change_returns_medium_risk() -> None:
    context = PullRequestContext(
        current_branch="feature/dependencies",
        base_branch="main",
        merge_base="abc123",
        commits=[],
        changed_files=[
            "pyproject.toml",
            "requirements.txt",
        ],
        diff="",
    )

    service = PullRequestAnalysisService()
    analysis = service.analyze(context)

    assert analysis.risk_level == RiskLevel.MEDIUM
    assert ChangeCategory.DEPENDENCY in analysis.change_categories
    assert "dependencies" in analysis.changed_areas
    assert "dependency and package changes" in analysis.reviewer_focus


def test_analyze_provider_change_returns_medium_risk() -> None:
    context = PullRequestContext(
        current_branch="feature/provider",
        base_branch="main",
        merge_base="abc123",
        commits=[],
        changed_files=[
            "src/diffsage/providers/gemini_provider.py",
            "src/diffsage/providers/base.py",
        ],
        diff="",
    )

    service = PullRequestAnalysisService()
    analysis = service.analyze(context)

    assert analysis.risk_level == RiskLevel.MEDIUM
    assert ChangeCategory.PROVIDER in analysis.change_categories
    assert "provider/integration areas" in analysis.changed_areas
    assert "provider and integration changes" in analysis.reviewer_focus
    assert analysis.change_categories.count(ChangeCategory.PROVIDER) == 1
    assert analysis.changed_areas.count("provider/integration areas") == 1


def test_analyze_configuration_change_returns_medium_risk() -> None:
    context = PullRequestContext(
        current_branch="feature/config",
        base_branch="main",
        merge_base="abc123",
        commits=[],
        changed_files=[
            "src/diffsage/config/settings.py",
        ],
        diff="",
    )

    service = PullRequestAnalysisService()
    analysis = service.analyze(context)

    assert analysis.risk_level == RiskLevel.MEDIUM
    assert ChangeCategory.CONFIGURATION in analysis.change_categories
    assert "configuration" in analysis.changed_areas
    assert "configuration and settings" in analysis.reviewer_focus


def test_analyze_authentication_change_returns_high_risk() -> None:
    context = PullRequestContext(
        current_branch="feature/auth",
        base_branch="main",
        merge_base="abc123",
        commits=[],
        changed_files=[
            "src/diffsage/services/credentials_service.py",
        ],
        diff="",
    )

    service = PullRequestAnalysisService()
    analysis = service.analyze(context)

    assert analysis.risk_level == RiskLevel.HIGH
    assert ChangeCategory.AUTHENTICATION in analysis.change_categories
    assert "authentication/security areas" in analysis.changed_areas
    assert "authentication and security-related changes" in analysis.reviewer_focus


def test_analyze_public_interface_change_returns_high_risk() -> None:
    context = PullRequestContext(
        current_branch="feature/api",
        base_branch="main",
        merge_base="abc123",
        commits=[],
        changed_files=[
            "src/app/api/users.py",
        ],
        diff="",
    )

    service = PullRequestAnalysisService()
    analysis = service.analyze(context)

    assert analysis.risk_level == RiskLevel.HIGH
    assert ChangeCategory.PUBLIC_INTERFACE in analysis.change_categories
    assert "interface-related areas" in analysis.changed_areas
    assert "public interface changes" in analysis.reviewer_focus


def test_analyze_authentication_and_provider_change_returns_high_risk() -> None:
    context = PullRequestContext(
        current_branch="feature/auth-provider",
        base_branch="main",
        merge_base="abc123",
        commits=[],
        changed_files=[
            "src/auth/service.py",
            "src/integrations/payment.py",
        ],
        diff="",
    )

    service = PullRequestAnalysisService()
    analysis = service.analyze(context)

    assert ChangeCategory.AUTHENTICATION in analysis.change_categories
    assert ChangeCategory.PROVIDER in analysis.change_categories
    assert analysis.risk_level == RiskLevel.HIGH


def test_analyze_public_interface_and_dependency_change_returns_high_risk() -> None:
    context = PullRequestContext(
        current_branch="feature/api",
        base_branch="main",
        merge_base="abc123",
        commits=[],
        changed_files=[
            "api/routes.py",
            "package.json",
        ],
        diff="",
    )

    service = PullRequestAnalysisService()
    analysis = service.analyze(context)

    assert ChangeCategory.PUBLIC_INTERFACE in analysis.change_categories
    assert ChangeCategory.DEPENDENCY in analysis.change_categories
    assert analysis.risk_level == RiskLevel.HIGH


def test_analyze_provider_and_test_change_returns_medium_risk() -> None:
    context = PullRequestContext(
        current_branch="feature/provider-tests",
        base_branch="main",
        merge_base="abc123",
        commits=[],
        changed_files=[
            "src/integrations/payment.py",
            "tests/integrations/test_payment.py",
        ],
        diff="",
    )

    service = PullRequestAnalysisService()
    analysis = service.analyze(context)

    assert ChangeCategory.PROVIDER in analysis.change_categories
    assert ChangeCategory.TEST in analysis.change_categories
    assert analysis.risk_level == RiskLevel.MEDIUM


def test_analyze_documentation_and_test_changes_returns_low_risk() -> None:
    context = PullRequestContext(
        current_branch="feature/docs-tests",
        base_branch="main",
        merge_base="abc123",
        commits=[],
        changed_files=[
            "README.md",
            "tests/test_example.py",
        ],
        diff="",
    )

    service = PullRequestAnalysisService()
    analysis = service.analyze(context)

    assert ChangeCategory.DOCUMENTATION in analysis.change_categories
    assert ChangeCategory.TEST in analysis.change_categories
    assert analysis.risk_level == RiskLevel.LOW


def analyze_files(*files: str):
    context = PullRequestContext(
        current_branch="feature/x",
        base_branch="main",
        merge_base="abc123",
        commits=[],
        changed_files=list(files),
        diff="",
    )

    return PullRequestAnalysisService().analyze(context)


@pytest.mark.parametrize(
    "file",
    ["AUTHORS", "src/author_profile.py", "src/authority.py", "lib/coauthors/list.py"],
)
def test_words_that_only_contain_auth_are_not_authentication(file) -> None:
    """Regression: "auth" was matched as a substring, so AUTHORS made a PR HIGH risk."""

    analysis = analyze_files(file)

    assert ChangeCategory.AUTHENTICATION not in analysis.change_categories
    assert analysis.risk_level == RiskLevel.LOW


@pytest.mark.parametrize(
    "file",
    [
        "src/auth.py",
        "app/AuthService.java",
        "src/login_view.py",
        "src/diffsage/storage/credentials_repository.py",
        "src/security/headers.py",
        "lib/oauth2/client.py",
    ],
)
def test_authentication_paths_are_high_risk(file) -> None:
    analysis = analyze_files(file)

    assert ChangeCategory.AUTHENTICATION in analysis.change_categories
    assert analysis.risk_level == RiskLevel.HIGH


@pytest.mark.parametrize(
    "file",
    [
        "src/app/tests/test_models.py",
        "test/helpers.py",
        "web/__tests__/button.js",
        "web/src/button.test.tsx",
        "web/src/button.spec.ts",
        "pkg/store/store_test.go",
        "src/main/java/UserServiceTest.java",
        "Api/UserTests.cs",
        "spec/models/user_spec.rb",
        "conftest.py",
    ],
)
def test_test_files_are_recognised_anywhere(file) -> None:
    """Regression: only tests/ at the top level and a top-level test_* file counted."""

    assert ChangeCategory.TEST in analyze_files(file).change_categories


@pytest.mark.parametrize("file", ["src/contest.py", "src/latest.py", "src/testing_utils.py"])
def test_names_that_only_contain_test_are_not_tests(file) -> None:
    assert ChangeCategory.TEST not in analyze_files(file).change_categories


@pytest.mark.parametrize(
    "file", ["tests/test_auth.py", "docs/authentication.md", "src/auth/README.md"]
)
def test_tests_and_docs_about_risky_areas_are_not_risky(file) -> None:
    """Regression: tests/test_auth.py or docs/authentication.md made a PR HIGH risk."""

    analysis = analyze_files(file)

    assert ChangeCategory.AUTHENTICATION not in analysis.change_categories
    assert analysis.risk_level == RiskLevel.LOW


@pytest.mark.parametrize("file", ["src/diffsage/commands/pr.py", "src/tool/cli/main.py"])
def test_command_line_changes_are_medium_not_high_risk(file) -> None:
    """Regression: every change under commands/ was HIGH risk, so every DiffSage PR was."""

    analysis = analyze_files(file)

    assert ChangeCategory.COMMAND_LINE in analysis.change_categories
    assert ChangeCategory.PUBLIC_INTERFACE not in analysis.change_categories
    assert analysis.risk_level == RiskLevel.MEDIUM


@pytest.mark.parametrize(
    "file", ["src/app/api/users.py", "server/routes/index.ts", "schema.graphql", "api.proto"]
)
def test_network_api_changes_are_high_risk(file) -> None:
    analysis = analyze_files(file)

    assert ChangeCategory.PUBLIC_INTERFACE in analysis.change_categories
    assert analysis.risk_level == RiskLevel.HIGH
