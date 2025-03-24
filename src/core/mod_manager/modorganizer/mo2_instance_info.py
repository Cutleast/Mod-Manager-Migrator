"""
Copyright (c) Cutleast
"""

from dataclasses import dataclass
from pathlib import Path

from ..instance_info import InstanceInfo


@dataclass(frozen=True)
class MO2InstanceInfo(InstanceInfo):
    """
    Class for identifying an MO2 instance and profile.
    """

    profile: str
    """
    The selected profile of the instance.
    """

    is_global: bool
    """
    Whether the instance is a global or portable instance.
    """

    base_folder: Path
    """
    Path to the base directory of the instance.
    **The folder must contain the instance's ModOrganizer.ini file!**
    """

    mods_folder: Path
    """
    Path to the instance's "mods" folder.
    """

    profiles_folder: Path
    """
    Path to the instance's "profiles" folder.
    """

    install_mo2: bool = True
    """
    Whether to install Mod Organizer 2 to the instance
    (only relevant for portable destination instances).
    """

    use_root_builder: bool = True
    """
    Whether to use the root builder MO2 plugin for mods with
    files for the game's root folder.
    MMM won't download the root builder plugin itself but will construct the respective 
    folder structures for root files instead of copying them to the real game folder.
    """
