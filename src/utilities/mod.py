"""
This file is part of Mod Manager Migrator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Mod:
    """
    Class for mods.
    Contains mod data like name, path, metadata, files and size.
    """

    name: str  # full mod name
    path: Path  # path of source mod folder
    metadata: dict  # metadata
    files: list[Path]  # list of all files
    size: int  # size of all files
    enabled: bool  # state in mod manager (True or False)
    installed: bool  # state in instance (True or False)
    selected: bool = True  # True: mod is migrated; False: mod is ignored

    overwriting_mods: list["Mod"] = field(default_factory=lambda: [])  # list of overwriting mods
    overwriting_files: list[Path] = field(default_factory=lambda: [])  # list of overwriting files (Vortex)
    overwritten_files: list[Path] = field(default_factory=lambda: [])  # list of overwritten files (MO2)

    def __repr__(self):
        return self.name

    def __str__(self):
        return self.name

    def set_enabled(self, enabled: bool):
        self.enabled = enabled

    def set_selected(self, selected: bool):
        self.selected = selected
    
    def __hash__(self):
        return hash((self.name, self.path, self.size))
