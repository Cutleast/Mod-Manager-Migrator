"""
Copyright (c) Cutleast
"""

from dataclasses import dataclass, field

from core.instance.mod import Mod
from core.instance.tool import Tool


@dataclass
class MigrationReport:
    """
    Class for a migration report.
    Contains information about the failed mods, tools and other errors.
    """

    failed_mods: dict[Mod, Exception] = field(default_factory=dict)
    """Map of failed mods and their exceptions."""

    failed_tools: dict[Tool, Exception] = field(default_factory=dict)
    """Map of failed tools and their exceptions."""

    other_errors: dict[str, Exception] = field(default_factory=dict)
    """Map of display name of errors and their exceptions."""

    @property
    def has_errors(self) -> bool:
        """Whether the report contains errors in any category."""

        return bool(self.failed_mods or self.failed_tools or self.other_errors)
