"""
Copyright (c) Cutleast
"""

import logging
import winreg
from abc import ABC
from pathlib import Path
from typing import Optional

from core.utilities.exceptions import GameNotFoundError


class Game(ABC):
    """
    Base class for general game specifications.
    """

    icon_name: str
    """
    Name of the icon resource to display.
    """

    name: str
    """
    Display name of the game.
    """

    id: str
    """
    Game identifier, should match the one used by Vortex.
    """

    nexus_id: str
    """
    Name of the game's nexus page (eg. "skyrimspecialedition").
    """

    installdir: Optional[Path] = None
    """
    Path to the game's install directory.
    """

    inidir: Path
    """
    Path to the game's ini directory.
    """

    inifiles: list[Path]
    """
    Paths to the game's ini files.
    """

    additional_files: list[str] = []
    """
    List of additional files to include in the migration.
    These filenames are relative to the respective mod manager's profiles folder.
    """

    reg_paths: list[str]
    """
    Registry keys to lookup the game's install directory.
    """

    log: logging.Logger

    def __init__(self) -> None:
        # Initialize class specific logger
        self.log = logging.getLogger(self.id)

    def get_install_dir(self) -> Path:
        """
        Attempts to get the game's install directory from the registry.

        Raises:
            GameNotFoundError: when the game's install directory could not be found

        Returns:
            Path: Path to the game's install directory
        """

        installdir = self.installdir

        # Only search for installdir if not already done
        if installdir is None:
            # Try to get Skyrim path from Steam if installed
            for reg_path in self.reg_paths:
                try:
                    key_str, reg_path = reg_path.split("\\", 1)
                    reg_path, value_name = reg_path.rsplit("\\", 1)
                    key: int = getattr(winreg, key_str, winreg.HKEY_LOCAL_MACHINE)
                    with winreg.OpenKey(key, reg_path) as hkey:
                        installdir = Path(winreg.QueryValueEx(hkey, value_name)[0])

                        if installdir.is_dir() and str(installdir) != ".":
                            self.installdir = installdir
                            return self.installdir

                except Exception as ex:
                    self.log.error(
                        f"Failed to get install path from registry key {reg_path!r}: {ex}"
                    )

        if self.installdir is None:
            raise GameNotFoundError(f"Failed to get install path for {self.name}")

        self.log.debug(f"Game install path: {self.installdir}")

        return self.installdir
