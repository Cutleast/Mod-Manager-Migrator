"""
Copyright (c) Cutleast
"""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Metadata:
    """
    Class for holding mod metadata like mod id, file id, etc.
    """

    mod_id: Optional[int]
    """
    Nexus Mods ID.
    """

    file_id: Optional[int]
    """
    Nexus Mods File ID.
    """

    version: str
    """
    Mod version.
    """

    file_name: Optional[str]
    """
    Full file name of the downloaded archive (eg. from Nexus Mods)
    or `None` if the installation is unknown or if there is none.
    """

    game_id: str
    """
    Nexus Mods Game ID (eg. "skyrimspecialedition").
    """

    def __hash__(self) -> int:
        return hash((self.mod_id, self.file_id, self.version, self.file_name))
