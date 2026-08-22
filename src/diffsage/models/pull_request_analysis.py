from dataclasses import dataclass, field
from enum import Enum


class ChangeCategory(str, Enum):
    AUTHENTICATION = "authentication"
    CONFIGURATION = "configuration"
    PROVIDER = "provider"
    DEPENDENCY = "dependency"
    PUBLIC_INTERFACE = "public_interface"
    TEST = "test"
    DOCUMENTATION = "documentation"


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass(slots=True)
class PullRequestAnalysis:
    """Represents deterministic analysis of a pull request change."""

    changed_areas: list[str] = field(default_factory=list)
    change_categories: list[ChangeCategory] = field(default_factory=list)
    risk_signals: list[str] = field(default_factory=list)
    risk_level: RiskLevel = RiskLevel.LOW
    reviewer_focus: list[str] = field(default_factory=list)
