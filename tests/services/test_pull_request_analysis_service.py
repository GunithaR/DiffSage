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
        current_branch="feature/cli",
        base_branch="main",
        merge_base="abc123",
        commits=[],
        changed_files=[
            "src/diffsage/commands/pr.py",
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
