from enum import Enum

class ConfigScope(str, Enum):
    """Scope of a configuration operation."""

    GLOBAL = "global"
    LOCAL = "local"