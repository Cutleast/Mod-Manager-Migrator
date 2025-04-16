"""
Copyright (c) Cutleast
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Optional, override

from core.utilities.cache import cache

from .metadata import Metadata


@dataclass
class Mod:
    """
    Class for representing a mod.
    """

    display_name: str
    """
    Display name of the mod.
    """

    path: Path
    """
    Path to source mod folder.
    """

    deploy_path: Optional[Path]
    """
    Path where the mod should be deployed, relative to the game folder.
    Defaults to the game's default mod folder if None.
    """

    metadata: Metadata
    """
    Metadata of the mod.
    """

    installed: bool
    """
    If the mod is installed.
    """

    enabled: bool
    """
    If the mod is enabled.
    """

    class Type(Enum):
        """
        Type of the mod.
        """

        Regular = auto()
        """
        The mod is a regular mod.
        """

        Separator = auto()
        """
        The mod is a separator.
        """

    mod_type: Type = Type.Regular
    """
    Type of the mod.
    """

    mod_conflicts: list["Mod"] = field(default_factory=list)
    """
    List of mods that overwrite this mod.
    These conflicts are used for creating a loadorder.
    """

    file_conflicts: dict[str, "Mod"] = field(default_factory=dict)
    """
    Mapping of file names that are explicitly overwritten by other mods.
    Each file is handled separately and has no impact on the loadorder.
    """

    @property
    @cache
    def files(self) -> list[Path]:
        """
        List of files.
        """

        return [
            file.relative_to(self.path)
            for file in self.path.rglob("*")
            if file.is_file()
        ]

    @property
    @cache
    def size(self) -> int:
        """
        Total size of all files.
        """

        return sum((self.path / file).stat().st_size for file in self.files)

    @cache
    def get_modpage_url(self) -> Optional[str]:
        """
        Gets the modpage URL of the mod if it has one.

        Returns:
            Optional[str]: The modpage URL of the mod if it has one, otherwise None.
        """

        base_url = "https://www.nexusmods.com"

        mod_id: Optional[int] = self.metadata.mod_id
        file_id: Optional[int] = self.metadata.file_id
        game_id: str = self.metadata.game_id

        if not mod_id:
            return None

        url = f"{base_url}/{game_id}/mods/{mod_id}"
        if file_id:
            url += f"?tab=files&file_id={file_id}"

        return url

    @override
    def __hash__(self) -> int:
        return hash((self.path, self.metadata))
