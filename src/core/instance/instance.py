"""
Copyright (c) Cutleast
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from .mod import Mod
from .tool import Tool


@dataclass
class Instance:
    """
    Class for representing an entire modinstance.
    """

    display_name: str
    """
    The name that is visible to the user.
    """

    game_folder: Path
    """
    The path to the instance's game folder.
    """

    mods: list[Mod]
    """
    List of the instance's mods.
    """

    tools: list[Tool]
    """
    List of the instance's tools.
    """

    last_tool: Optional[Tool] = None
    """
    (Optional) last tool that was executed/selected in the instance.
    """

    order_matters: bool = False
    """
    Whether the mods have a fixed order that matters.
    """

    separate_ini_files: bool = True
    """
    Whether the instance has its own separate ini files.
    """

    separate_save_games: bool = True
    """
    Whether the instance has its own separate save games.
    """

    def is_mod_installed(self, mod: Mod) -> bool:
        """
        Checks if a mod is already installed in this instance.

        Args:
            mod (Mod): The mod to check.

        Returns:
            bool: `True` if the mod is installed, `False` otherwise
        """

        mod_id: Optional[int] = mod.metadata.mod_id
        file_id: Optional[int] = mod.metadata.file_id

        return (
            any(
                (mod_id == m.metadata.mod_id and mod_id is not None)
                and (file_id == m.metadata.file_id and file_id is not None)
                for m in self.mods
            )
            or mod in self.mods
        )

    def get_installed_mod(self, mod: Mod) -> Mod:
        """
        Returns a mod from the instance matching the specified mod.

        Args:
            mod (Mod): The mod to get.

        Raises:
            ValueError: If the mod is not installed

        Returns:
            Mod: The matching mod
        """

        if mod in self.mods:
            return self.mods[self.mods.index(mod)]

        if mod.metadata.mod_id is None or mod.metadata.file_id is None:
            raise ValueError("Mod id and file id required for identifying mod!")

        installed_mods: dict[tuple[int, int], Mod] = {
            (m.metadata.mod_id, m.metadata.file_id): m
            for m in self.mods
            if m.metadata.mod_id is not None and m.metadata.file_id is not None
        }

        if (mod.metadata.mod_id, mod.metadata.file_id) in installed_mods:
            return installed_mods[(mod.metadata.mod_id, mod.metadata.file_id)]

        raise ValueError("Mod not installed!")

    @property
    def loadorder(self) -> list[Mod]:
        """
        List of mods sorted alphabetically and after their mod conflicts
        (overwritten mods before overwriting mods).
        """

        return self.get_loadorder()

    def get_loadorder(self, order_matters: Optional[bool] = None) -> list[Mod]:
        """
        Sorts the mods in this instance if `order_matters` is not `True`.

        Args:
            order_matters (Optional[bool], optional):
                Whether the mods have a fixed order. Defaults to the instance's default.

        Returns:
            list[Mod]: The sorted list of mods
        """

        if order_matters is None:
            order_matters = self.order_matters

        if order_matters:
            return self.mods.copy()

        new_loadorder: list[Mod] = self.mods.copy()
        new_loadorder.sort(key=lambda m: m.display_name)

        for mod in filter(lambda m: m.mod_conflicts, self.mods):
            if mod.mod_conflicts:
                old_index = index = new_loadorder.index(mod)

                # Get smallest index of all overwriting mods
                overwriting_mods = [
                    new_loadorder.index(self.get_installed_mod(overwriting_mod))
                    for overwriting_mod in mod.mod_conflicts
                ]
                index = min(overwriting_mods)

                if old_index > index:
                    new_loadorder.insert(index, new_loadorder.pop(old_index))

        return new_loadorder

    @property
    def size(self) -> int:
        """
        The total size of all mods in this instance.
        """

        return sum(mod.size for mod in self.mods)
