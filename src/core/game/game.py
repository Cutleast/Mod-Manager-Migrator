"""
Copyright (c) Cutleast
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, Any, override

from pydantic import AfterValidator, BaseModel, Field

from core.utilities.cache import cache
from core.utilities.env_resolver import resolve
from core.utilities.filesystem import get_documents_folder
from core.utilities.qt_res_provider import load_json_resource


class Game(BaseModel):
    """
    Base class for general game specifications.
    """

    id: str
    """
    Game identifier, should match the one used by Vortex (eg. "skyrimse").
    """

    display_name: str
    """
    Display name of the game (eg. "Skyrim Special Edition").
    """

    short_name: str
    """
    Short name of the game (eg. "SkyrimSE").
    """

    nexus_id: str
    """
    Name of the game's nexus page (eg. "skyrimspecialedition").
    """

    inidir: Annotated[
        Path,
        AfterValidator(lambda p: resolve(p, documents=str(get_documents_folder()))),
    ]
    """
    Path to the game's ini directory.
    Variables like `%%DOCUMENTS%%` are automatically resolved.
    """

    inifiles: Annotated[
        list[Path],
        AfterValidator(
            lambda f: [resolve(f, documents=str(get_documents_folder())) for f in f]
        ),
    ]
    """
    Paths to the game's ini files, relative to `inidir`.
    Variables like `%%DOCUMENTS%%` are automatically resolved.
    """

    mods_folder: Path
    """
    The game's default folder for mods, relative to its install directory.
    """

    additional_files: list[str] = Field(default_factory=list)
    """
    List of additional files to include in the migration.
    These filenames are relative to the respective mod manager's profiles folder.
    """

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

    @staticmethod
    @cache
    def get_game_by_short_name(short_name: str) -> Game:
        """
        Gets a game by its short name.

        Args:
            short_name (str): Game short name

        Raises:
            ValueError: when the game could not be found

        Returns:
            Game: Game with specified short name
        """

        games: dict[str, Game] = {
            game.short_name: game for game in Game.get_supported_games()
        }

        if short_name in games:
            return games[short_name]

        raise ValueError(f"Game '{short_name}' not found!")

    @override
    def __hash__(self) -> int:
        return hash((self.id, self.display_name, self.short_name, self.nexus_id))
