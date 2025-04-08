"""
Copyright (c) Cutleast
"""

import json
from pathlib import Path
from typing import Any

import pytest
from pyfakefs.fake_filesystem import FakeFilesystem

from core.config.app_config import AppConfig
from core.game.game import Game
from core.instance.instance import Instance
from core.instance.mod import Mod
from core.migrator.file_blacklist import FileBlacklist
from core.mod_manager.vortex.exceptions import VortexNotFullySetupError
from core.mod_manager.vortex.profile_info import ProfileInfo
from core.mod_manager.vortex.vortex import Vortex
from core.utilities.env_resolver import resolve
from core.utilities.leveldb import LevelDB
from tests.utils import Utils

from .._setup.mock_plyvel import MockPlyvelDB
from ..base_test import BaseTest


class TestVortex(BaseTest):
    """
    Tests `core.mod_manager.vortex.Vortex`.
    """

    DATABASE: tuple[str, type[LevelDB]] = ("level_db", LevelDB)
    RAW_DATA: tuple[str, type[dict[bytes, bytes]]] = ("data", dict)

    def test_load_instance(
        self,
        data_folder: Path,
        app_config: AppConfig,
        vortex_profile_info: ProfileInfo,
        full_vortex_db: MockPlyvelDB,
        test_fs: FakeFilesystem,
    ) -> None:
        """
        Tests `core.mod_manager.modorganizer.modorganizer.ModOrganizer.load_instance()`.
        """

        test_fs.add_real_directory(
            data_folder / "skyrimse",
            target_path=resolve(Path("%APPDATA%")) / "Vortex" / "skyrimse",
        )

        # given
        vortex = Vortex()
        vortex.db_path.mkdir(parents=True, exist_ok=True)
        vortex_profile_info.game.installdir = Path(
            "E:\\SteamLibrary\\Skyrim Special Edition"
        )
        vortex_profile_info.game.installdir.mkdir(parents=True, exist_ok=True)

        # when
        instance: Instance = vortex.load_instance(
            vortex_profile_info, app_config.modname_limit, FileBlacklist.get_files()
        )

        # then
        assert len(instance.mods) == 7

        # test mod name length limit
        assert all(
            len(mod.display_name) <= app_config.modname_limit for mod in instance.mods
        )

        # when
        obsidian_weathers: Mod = self.get_mod_by_name(
            "Obsidian Weathers and Seasons", instance
        )
        obsidian_weathers_german: Mod = self.get_mod_by_name(
            "Obsidian Weathers and Seasons - German", instance
        )

        # then
        assert obsidian_weathers.mod_conflicts == [obsidian_weathers_german]
        assert obsidian_weathers_german.mod_conflicts == []
        assert obsidian_weathers.file_conflicts == {}
        assert obsidian_weathers_german.file_conflicts == {}

        # when
        wet_and_cold: Mod = self.get_mod_by_name("Wet and Cold SE", instance)
        wet_and_cold_german: Mod = self.get_mod_by_name(
            "Wet and Cold SE - German", instance
        )

        # then
        assert (
            wet_and_cold_german.file_conflicts["scripts\\_wetskyuiconfig.pex"]
            == wet_and_cold
        )

    def test_create_instance(
        self, test_fs: FakeFilesystem, ready_vortex_db: MockPlyvelDB, qt_resources: None
    ) -> None:
        """
        Tests `core.mod_manager.vortex.Vortex.create_instance()`
        """

        # given
        vortex = Vortex()
        vortex.db_path.mkdir(parents=True, exist_ok=True)
        database: LevelDB = Utils.get_private_field(vortex, *TestVortex.DATABASE)
        profile_info = ProfileInfo(
            display_name="Test profile",
            game=Game.get_game_by_id("skyrimse"),
            id="1a2b3c4d",
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

        # when
        vortex.create_instance(profile_info)
        profile_data: dict[str, Any] = database.load(prefix)["persistent"]["profiles"][
            profile_info.id
        ]
        profile_data.pop("lastActivated")  # remove unique timestamp

        # then
        assert profile_data == expected_profile_data

        # when
        raw_data: dict[bytes, bytes] = Utils.get_private_field(
            ready_vortex_db, *TestVortex.RAW_DATA
        )
        profile_prefix: bytes = prefix.encode()

        # then
        assert (
            raw_data[profile_prefix + b"features###local_game_settings"]
            == json.dumps(False).encode()
        )
        assert (
            raw_data[profile_prefix + b"features###local_saves"]
            == json.dumps(False).encode()
        )
        assert raw_data[profile_prefix + b"gameId"] == json.dumps("skyrimse").encode()
        assert raw_data[profile_prefix + b"id"] == json.dumps(profile_info.id).encode()
        assert (
            raw_data[profile_prefix + b"name"]
            == json.dumps(profile_info.display_name).encode()
        )

    def test_vortex_not_installed(
        self, empty_vortex_db: MockPlyvelDB, qt_resources: None
    ) -> None:
        """
        Tests if `core.mod_manager.vortex.Vortex` raises a `VortexNotInstalledError`
        when running a pre-migration check on an empty Vortex database.
        """

        # given
        vortex = Vortex()
        Utils.get_private_field(vortex, *TestVortex.DATABASE).use_symlink = False
        profile_info = ProfileInfo(
            display_name="Test profile",
            game=Game.get_game_by_id("skyrimse"),
            id=ProfileInfo.generate_id(),
        )

        # then
        with pytest.raises(VortexNotFullySetupError):
            vortex.prepare_migration(profile_info)

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

    def test_install_mod(
        self,
        app_config: AppConfig,
        test_fs: FakeFilesystem,
        ready_vortex_db: MockPlyvelDB,
        instance: Instance,
        qt_resources: None,
    ) -> None:
        """
        Tests `core.mod_manager.vortex.Vortex.install_mod()`.
        """

        self.test_create_instance(test_fs, ready_vortex_db, qt_resources)

        # given
        vortex = Vortex()
        database: LevelDB = Utils.get_private_field(vortex, *TestVortex.DATABASE)
        database.path.mkdir(parents=True, exist_ok=True)
        profile_info = ProfileInfo(
            display_name="Test profile (1a2b3c4d)",
            game=Game.get_game_by_id("skyrimse"),
            id="1a2b3c4d",
        )
        dst_profile: Instance = vortex.load_instance(
            profile_info, app_config.modname_limit, FileBlacklist.get_files()
        )
        mod = instance.mods[1]

        # when
        vortex.install_mod(
            mod,
            dst_profile,
            profile_info,
            file_redirects={},
            use_hardlinks=True,
            replace=True,
        )

        # then
        dst_profile = vortex.load_instance(
            profile_info, app_config.modname_limit, FileBlacklist.get_files()
        )
        assert dst_profile.mods[-1].metadata == mod.metadata

    def test_format_utc_timestamp(self) -> None:
        """
        Tests `core.mod_manager.vortex.Vortex.format_utc_timestamp()`.
        """

        # given
        timestamp: float = 1743321182.5131004
        expected_result: str = "2025-03-30T07:53:02.513100Z"

        # when
        actual_result: str = Vortex.format_utc_timestamp(timestamp)

        # then
        assert actual_result == expected_result

    def test_format_unix_timestamp(self) -> None:
        """
        Tests `core.mod_manager.vortex.Vortex.format_unix_timestamp()`.
        """

        # given
        timestamp: float = 1743321182.5131004
        expected_result: int = 1743321182513

        # when
        actual_result: int = Vortex.format_unix_timestamp(timestamp)

        # then
        assert actual_result == expected_result
