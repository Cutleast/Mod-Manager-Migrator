"""
Copyright (c) Cutleast
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from .mod import Mod


@dataclass
class Tool:
    """
    Class for representing modding tools.
    """

    display_name: str
    """
    The name that is displayed in the mod manager's ui.
    """

    mod: Optional[Mod]
    """
    The mod that contains the executable of this tool 
    or None if the tool is outside of the modinstance.
    """

    executable: Path
    """
    The path to the executable, relative to the folder of its mod
    or absolute if the tool is outside of the modinstance.
    """

    commandline_args: list[str]
    """
    The commandline arguments to pass to the executable.
    """

    working_dir: Path
    """
    The working directory, the tool should be executed in.
    (Usually the game folder itself)
    """

    is_in_game_dir: bool
    """
    Whether the tool is in the game folder or not.
    This controls whether the tool gets copied with the game folder, if selected by
    the user (WIP).
    """
