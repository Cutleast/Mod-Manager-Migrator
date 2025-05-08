"""
Copyright (c) Cutleast
"""

from __future__ import annotations

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

        Overwrite = auto()
        """
        The mod represents the overwrite folder of an MO2 instance.
        """

    mod_type: Type = Type.Regular
    """
    Type of the mod.
    """

    mod_conflicts: list[Mod] = field(default_factory=list)
    """
    List of mods that overwrite this mod.
    These conflicts are used for creating a loadorder.
    """

    file_conflicts: dict[str, Mod] = field(default_factory=dict)
    """
    Mapping of file names that are explicitly overwritten by other mods.
    Each file is handled separately and has no impact on the loadorder.
    """

    @property
    def files(self) -> list[Path]:
        """
        List of files.
        """

        return Mod.__get_files(self.path)

    @staticmethod
    @cache
    def __get_files(path: Path) -> list[Path]:
        return [file.relative_to(path) for file in path.rglob("*") if file.is_file()]

    @staticmethod
    def copy(mod: Mod) -> Mod:
        """
        Creates a copy of the specified mod.
        Resets the cache of the files and size properties.

        Args:
            mod (Mod): Mod to copy

        Returns:
            Mod: Copied mod instance
        """

        return Mod(
            display_name=mod.display_name,
            path=mod.path,
            deploy_path=mod.deploy_path,
            metadata=mod.metadata,
            installed=mod.installed,
            enabled=mod.enabled,
            mod_type=mod.mod_type,
            mod_conflicts=mod.mod_conflicts,
            file_conflicts=mod.file_conflicts,
        )

    @property
    def size(self) -> int:
        """
        Total size of all files.
        """

        return Mod.__get_size(self.path)

    @staticmethod
    @cache
    def __get_size(path: Path) -> int:
        return sum((path / file).stat().st_size for file in Mod.__get_files(path))

    @cache
    def get_modpage_url(self, direct: bool = False) -> Optional[str]:
        """
        Gets the modpage URL of the mod if it has one.

        Args:
            direct (bool, optional):
                If True, the modpage URL will include the file ID.
                Defaults to False.

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
        if file_id and direct:
            url += f"?tab=files&file_id={file_id}"

        return url

    @override
    def __hash__(self) -> int:
        return hash((self.path, self.metadata))

    @override
    def __eq__(self, value: object) -> bool:
        if not isinstance(value, Mod):
            return False

        return hash(self) == hash(value)
