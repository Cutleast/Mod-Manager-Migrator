"""
Copyright (c) Cutleast
"""

import json
from pathlib import Path
from typing import Any

import pytest
from base_test import BaseTest
from pyfakefs.fake_filesystem import FakeFilesystem
from setup.mock_plyvel import MockPlyvelDB

from core.config.app_config import AppConfig
from core.game.game import Game
from core.instance.instance import Instance
from core.instance.mod import Mod
from core.instance.tool import Tool
from core.migrator.file_blacklist import FileBlacklist
from core.mod_manager.vortex.exceptions import VortexNotFullySetupError
from core.mod_manager.vortex.profile_info import ProfileInfo
from core.mod_manager.vortex.vortex import Vortex
from core.utilities.leveldb import LevelDB
from tests.utils import Utils


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

        # given
        vortex = Vortex()
        vortex.db_path.mkdir(parents=True, exist_ok=True)

        # when
        instance: Instance = vortex.load_instance(
            vortex_profile_info, app_config.modname_limit, FileBlacklist.get_files()
        )

        # then
        assert len(instance.mods) == 8
        assert len(instance.tools) == 3

        # test game folder
        assert instance.game_folder == Path("E:\\SteamLibrary\\Skyrim Special Edition")

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

        # when
        skse_loader: Tool = self.get_tool_by_name("Skyrim Script Extender 64", instance)
        dip: Tool = self.get_tool_by_name("DIP", instance)
        dip_mod: Mod = self.get_mod_by_name("Dynamic Interface Patcher - DIP", instance)

        # then
        assert skse_loader.executable == Path("skse64_loader.exe")
        assert skse_loader.mod is None
        assert skse_loader.commandline_args == []
        assert skse_loader.is_in_game_dir
        assert skse_loader.working_dir is None
        assert dip.executable == Path("DIP\\DIP.exe")
        assert dip.mod is dip_mod
        assert dip.commandline_args == []
        assert not dip.is_in_game_dir
        assert dip.working_dir is None

    def test_create_instance(
        self, test_fs: FakeFilesystem, ready_vortex_db: MockPlyvelDB
    ) -> None:
        """
        Tests `core.mod_manager.vortex.Vortex.create_instance()`
        """

        # given
        vortex = Vortex()
        vortex.db_path.mkdir(parents=True, exist_ok=True)
        game_folder = Path("E:\\SteamLibrary\\Skyrim Special Edition")
        database: LevelDB = Utils.get_private_field(vortex, *TestVortex.DATABASE)
        profile_info = ProfileInfo(
            display_name="Test profile",
            game=Game.get_game_by_id("skyrimse"),
            id="5e6f7g8h9j",
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
        vortex.create_instance(profile_info, game_folder)
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

    def test_vortex_not_installed(self, empty_vortex_db: MockPlyvelDB) -> None:
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
            id=Vortex.generate_id(),
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
    ) -> None:
        """
        Tests `core.mod_manager.vortex.Vortex.install_mod()`.
        """

        self.test_create_instance(test_fs, ready_vortex_db)

        # given
        vortex = Vortex()
        database: LevelDB = Utils.get_private_field(vortex, *TestVortex.DATABASE)
        database.path.mkdir(parents=True, exist_ok=True)
        profile_info = ProfileInfo(
            display_name="Test profile (5e6f7g8h9j)",
            game=Game.get_game_by_id("skyrimse"),
            id="5e6f7g8h9j",
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

    def test_is_instance_existing(
        self, full_vortex_db: MockPlyvelDB, vortex_profile_info: ProfileInfo
    ) -> None:
        """
        Tests `Vortex.is_instance_existing()`.
        """

        # given
        vortex = Vortex()
        vortex.db_path.mkdir(parents=True, exist_ok=True)

        # when/then
        assert vortex.is_instance_existing(vortex_profile_info)

        # when
        non_existing_profile = ProfileInfo(
            display_name="Non Existing Profile",
            game=vortex_profile_info.game,
            id="xyz1234",
        )

        # then
        assert not vortex.is_instance_existing(non_existing_profile)
