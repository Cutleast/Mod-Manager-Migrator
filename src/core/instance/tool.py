"""
Copyright (c) Cutleast
"""

from pathlib import Path
from typing import Optional, override

from pydantic.dataclasses import dataclass

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
    Relative to the game folder if `is_in_game_dir` is True.
    """

    commandline_args: list[str]
    """
    The commandline arguments to pass to the executable.
    """

    working_dir: Optional[Path]
    """
    The working directory, the tool should be executed in.
    (Usually the game folder itself if the path is None)
    """

    is_in_game_dir: bool
    """
    Whether the tool is in the game folder or not.
    This controls whether the tool gets copied with the game folder, if selected by
    the user (WIP).
    """

    def get_full_executable_path(self, game_folder: Optional[Path] = None) -> Path:
        """
        Returns the full path to the executable.

        Args:
            game_folder (Optional[Path], optional):
                The game folder (required if `is_in_game_dir` is True). Defaults to None.

        Returns:
            Path: The full path to the executable.
        """

        if self.mod is not None:
            return self.mod.path / self.executable
        elif self.is_in_game_dir:
            if game_folder is None:
                raise ValueError(
                    "Game folder not specified but tool is in game folder!"
                )

            return game_folder / self.executable
        else:
            return self.executable

    @override
    def __hash__(self) -> int:
        executable: Path = self.executable

        if self.mod is not None:
            executable = self.mod.path / executable

        return hash((executable, " ".join(self.commandline_args), self.working_dir))

    @override
    def __eq__(self, value: object) -> bool:
        if not isinstance(value, Tool):
            return False

        return hash(self) == hash(value)
