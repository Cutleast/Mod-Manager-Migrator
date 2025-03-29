"""
Copyright (c) Cutleast
"""

from __future__ import annotations

import logging
import winreg
from pathlib import Path
from typing import Annotated, Any, Optional

from pydantic import AfterValidator, BaseModel, Field

from core.utilities.cache import cache
from core.utilities.env_resolver import resolve
from core.utilities.filesystem import get_documents_folder
from core.utilities.qt_res_provider import load_json_resource

from .exceptions import GameNotFoundError


class Game(BaseModel):
    """
    Base class for general game specifications.
    """

    id: str
    """
    Game identifier, should match the one used by Vortex.
    """

    display_name: str
    """
    Display name of the game.
    """

    nexus_id: str
    """
    Name of the game's nexus page (eg. "skyrimspecialedition").
    """

    inidir: Annotated[
        Path, AfterValidator(lambda p: resolve(p, documents=get_documents_folder()))
    ]
    """
    Path to the game's ini directory.
    Variables like `%%DOCUMENTS%%` are automatically resolved.
    """

    inifiles: Annotated[
        list[Path],
        AfterValidator(
            lambda f: [resolve(f, documents=get_documents_folder()) for f in f]
        ),
    ]
    """
    Paths to the game's ini files, relative to `inidir`.
    Variables like `%%DOCUMENTS%%` are automatically resolved.
    """

    reg_paths: list[str]
    """
    Registry keys to lookup the game's install directory.
    """

    additional_files: list[str] = Field(default_factory=list)
    """
    List of additional files to include in the migration.
    These filenames are relative to the respective mod manager's profiles folder.
    """

    __log: logging.Logger = logging.getLogger("Game")
    __installdir: Optional[Path] = None

    @property
    def installdir(self) -> Path:
        """
        Attempts to get the game's install directory from the registry.

        Raises:
            GameNotFoundError: when the game's install directory could not be found

        Returns:
            Path: Path to the game's install directory
        """

        if self.__installdir is None:
            self.__log.info(f"Attempting to get install path for game '{self.id}'...")

            # Try to get game path from registry
            for reg_path in self.reg_paths:
                self.__log.debug(f"Fetching registry key '{reg_path}'...")
                try:
                    key_str, reg_path = reg_path.split("\\", 1)
                    reg_path, value_name = reg_path.rsplit("\\", 1)
                    key: int = getattr(winreg, key_str, winreg.HKEY_LOCAL_MACHINE)
                    with winreg.OpenKey(key, reg_path) as hkey:
                        installdir = Path(winreg.QueryValueEx(hkey, value_name)[0])

                    if installdir.is_dir() and str(installdir) != ".":
                        self.__log.debug(f"Game install path: {installdir}")
                        self.__installdir = installdir

                except FileNotFoundError:
                    self.__log.debug(f"Registry key '{reg_path}' does not exist.")

                except Exception as ex:
                    self.__log.error(
                        f"Failed to get install path from registry key '{reg_path}': {ex}"
                    )

        if self.__installdir is None:
            raise GameNotFoundError

        return self.__installdir

    @installdir.setter
    def installdir(self, path: Path) -> None:
        """
        Sets the game's install directory.

        Args:
            path (Path): Path to the game's install directory
        """

        self.__installdir = path
        self.__log.info(f"Set install path for game '{self.id}' to '{path}'.")

    @staticmethod
    @cache
    def get_supported_games() -> list[Game]:
        """
        Gets a list of supported games from the JSON resource.

        Returns:
            list[Game]: List of supported games
        """

        data: list[dict[str, Any]] = load_json_resource(":/games.json")

        return [Game.model_validate(game) for game in data]

    @staticmethod
    @cache
    def get_game_by_id(game_id: str) -> Game:
        """
        Gets a game by its id.

        Args:
            game_id (str): Game id

        Raises:
            ValueError: when the game could not be found

        Returns:
            Game: Game with specified id
        """

        games: dict[str, Game] = {game.id: game for game in Game.get_supported_games()}

        if game_id in games:
            return games[game_id]

        raise ValueError(f"Game '{game_id}' not found!")
