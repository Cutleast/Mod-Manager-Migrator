"""
Copyright (c) Cutleast
"""

import os
import sys
from typing import Any
from unittest.mock import patch

import pytest

sys.path.append(os.path.join(os.getcwd(), "src"))

from src.core.game.skyrimse import SkyrimSE
from src.core.mod_manager.vortex.profile_info import ProfileInfo
from src.core.mod_manager.vortex.vortex import Vortex
from src.core.utilities.leveldb import LevelDB

from .._setup.mock_path import MockPath
from .._setup.mock_plyvel import MockPlyvelDB
from ..base_test import BaseTest


class TestVortex(BaseTest):
    """
    Tests `core.mod_manager.vortex.Vortex`.
    """

    @patch("pathlib.WindowsPath", new=MockPath)
    def test_create_instance(self, mock_plyvel: MockPlyvelDB) -> None:
        """
        Tests `core.mod_manager.vortex.Vortex.create_instance()`
        """

        # given
        vortex = Vortex()
        database: LevelDB = vortex._Vortex__level_db
        database.use_symlink = False
        profile_info = ProfileInfo(
            display_name="Test profile",
            game=SkyrimSE(),
            id=ProfileInfo.generate_id(),
        )
        prefix: str = f"persistent###profiles###{profile_info.id}###"
        expected_profile_data: dict[str, Any] = {
            "features": {
                "local_game_settings": False,
                "local_saves": False,
            },
            "gameId": "skyrimse",
            "id": profile_info.id,
            "name": profile_info.display_name,
        }

        # then
        vortex.create_instance(profile_info)
        profile_data: dict[str, Any] = database.load(prefix)["persistent"]["profiles"][
            profile_info.id
        ]
        profile_data.pop("lastActivated")  # remove unique timestamp

        # when
        assert profile_data == expected_profile_data

    logical_file_name_data: list[tuple[str, int, str]] = [
        (
            "(Part 1) SSE Engine Fixes for 1.5.39 - 1.5.97-17230-5-9-1-1664974289.7z",
            17230,
            "(Part 1) SSE Engine Fixes for 1.5.39 - 1.5.97",
        ),
        (
            "(Part 2) Engine Fixes - skse64 Preloader and TBB Lib-17230-2020-3-1611367474.7z",
            17230,
            "(Part 2) Engine Fixes - skse64 Preloader and TBB Lib",
        ),
        (
            "Constructible Object Custom Keyword System NG-81731-1-1-1-1713893656.zip",
            81731,
            "Constructible Object Custom Keyword System NG",
        ),
        (
            "RaceMenu Anniversary Edition v0-4-19-16-19080-0-4-19-16-1706297897.7z",
            19080,
            "RaceMenu Anniversary Edition v0-4-19-16",
        ),
        ("Test Mod Name.7z", 0, "Test Mod Name"),
    ]

    @pytest.mark.parametrize(
        "file_name, mod_id, expected_logical_name", logical_file_name_data
    )
    def test_get_logical_file_name(
        self, file_name: str, mod_id: int, expected_logical_name: str
    ) -> None:
        """
        Tests `core.mod_manager.vortex.Vortex.get_logical_file_name()`
        """

        # when
        logical_file_name: str = Vortex.get_logical_file_name(file_name, mod_id)

        # then
        assert logical_file_name == expected_logical_name
