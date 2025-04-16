"""
Copyright (c) Cutleast
"""

from pathlib import Path
from typing import Any

import pytest
from pyfakefs.fake_filesystem import FakeFilesystem

from core.config.app_config import AppConfig
from core.game.game import Game
from core.instance.instance import Instance
from core.instance.metadata import Metadata
from core.instance.mod import Mod
from core.migrator.file_blacklist import FileBlacklist
from core.mod_manager.modorganizer.mo2_instance_info import MO2InstanceInfo
from core.mod_manager.modorganizer.modorganizer import ModOrganizer
from core.utilities.ini_file import INIFile
from tests.utils import Utils

from ..base_test import BaseTest


class TestModOrganizer(BaseTest):
    """
    Tests `core.mod_manager.modorganizer.modorganizer.ModOrganizer`.
    """

    @staticmethod
    def parse_meta_ini_stub(meta_ini_path: Path, default_game: Game) -> Metadata:
        """
        Stub for `core.mod_manager.modorganizer.modorganizer.ModOrganizer.__parse_meta_ini()`.
        """

        raise NotImplementedError

    PARSE_META_INI_DATA: list[tuple[Path, Metadata]] = [
        (
            Path("Test Mods_separator") / "meta.ini",
            Metadata(
                mod_id=None,
                file_id=None,
                version="",
                file_name=None,
                game_id="skyrimspecialedition",
            ),
        ),
        (
            Path("RS Children Overhaul") / "meta.ini",
            Metadata(
                mod_id=2650,
                file_id=128013,
                version="1.1.3",
                file_name="RSSE Children Overhaul 1.1.3 with hotfix 1-2650-1-1-3HF1-1583835543.7z",
                game_id="skyrimspecialedition",
            ),
        ),
    ]

    @pytest.mark.parametrize("meta_ini_path, expected_metadata", PARSE_META_INI_DATA)
    def test_parse_meta_ini(
        self,
        meta_ini_path: Path,
        expected_metadata: Metadata,
        data_folder: Path,
        qt_resources: None,
    ) -> None:
        """
        Tests `core.mod_manager.modorganizer.modorganizer.ModOrganizer.__parse_meta_ini()`.
        """

        # given
        mo2 = ModOrganizer()
        test_meta_ini_path: Path = data_folder / "mod_instance" / "mods" / meta_ini_path

        # when
        metadata: Metadata = Utils.get_private_method(
            mo2, "parse_meta_ini", TestModOrganizer.parse_meta_ini_stub
        )(
            meta_ini_path=test_meta_ini_path,
            default_game=Game.get_game_by_id("skyrimse"),
        )

        # then
        assert metadata == expected_metadata

    def test_load_instance(
        self, app_config: AppConfig, mo2_instance_info: MO2InstanceInfo
    ) -> None:
        """
        Tests `core.mod_manager.modorganizer.modorganizer.ModOrganizer.load_instance()`.
        """

        # given
        mo2 = ModOrganizer()

        # when
        instance: Instance = mo2.load_instance(
            mo2_instance_info, app_config.modname_limit, FileBlacklist.get_files()
        )

        # then
        assert len(instance.mods) == 8

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

    @staticmethod
    def process_conflicts_stub(mods: list[Mod], file_blacklist: list[str]) -> None:
        """
        Method stub for `ModOrganizer.__process_conflicts()`.
        """

        raise NotImplementedError

    def test_process_conflicts(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """
        Tests `ModOrganizer.__process_conflicts()`.
        """

        # given
        mo2 = ModOrganizer()
        mods: list[Mod] = [
            TestModOrganizer.create_blank_mod("test_mod_1"),
            TestModOrganizer.create_blank_mod("test_mod_2"),
            TestModOrganizer.create_blank_mod("test_mod_3"),
            TestModOrganizer.create_blank_mod("test_mod_4"),
            TestModOrganizer.create_blank_mod("test_mod_5"),
        ]
        file_index: dict[str, list[Mod]] = {
            "test_file_1": [mods[0], mods[2], mods[4]],
            "test_file_2": [mods[0], mods[1]],
            "test_file_2.mohidden": [mods[2]],
            "test_file_3": [mods[4]],
        }

        for i in range(
            100_000, 500_000
        ):  # simulate a large mod list with lots of files
            file_index[f"test_file_{i}"] = [mods[i // 100_000]]

            # add some hidden files
            if i % 5 == 0:
                file_index[f"hidden_test_file_{i}.mohidden"] = [mods[i // 100_000]]

        # when
        monkeypatch.setattr(
            ModOrganizer, "_index_modlist", lambda mods, file_blacklist: file_index
        )
        Utils.get_private_method(mo2, "process_conflicts", self.process_conflicts_stub)(
            mods, []
        )

        # then
        assert mods[0].mod_conflicts == [mods[2], mods[4], mods[1]]
        assert mods[1].mod_conflicts == []
        assert mods[2].mod_conflicts == [mods[4]]
        assert mods[3].mod_conflicts == []
        assert mods[4].mod_conflicts == []

        assert mods[2].file_conflicts["test_file_2"] == mods[1]

    def test_create_instance(self, test_fs: FakeFilesystem, qt_resources: None) -> None:
        """
        Tests `core.mod_manager.modorganizer.modorganizer.ModOrganizer.create_instance()`.
        """

        # given
        mo2 = ModOrganizer()
        game: Game = Game.get_game_by_id("skyrimse")
        game_folder = Path("E:\\SteamLibrary\\Skyrim Special Edition")
        test_instance_path = Path("E:\\Modding\\Test Instance")
        instance_data = MO2InstanceInfo(
            display_name="Test Instance",
            game=game,
            profile="Default",
            is_global=False,
            base_folder=test_instance_path,
            mods_folder=test_instance_path / "mods",
            profiles_folder=test_instance_path / "profiles",
            install_mo2=False,
        )

        # when
        instance: Instance = mo2.create_instance(instance_data, game_folder)

        # then
        assert instance.mods == []
        assert instance.tools == []
        assert instance_data.base_folder.is_dir()
        assert instance_data.mods_folder.is_dir()
        assert instance_data.profiles_folder.is_dir()
        assert (instance_data.base_folder / "ModOrganizer.ini").is_file()
        assert (instance_data.profiles_folder / instance_data.profile).is_dir()
        assert (
            instance_data.profiles_folder / instance_data.profile / "modlist.txt"
        ).is_file()

        # when
        ini_data: dict[str, Any] = INIFile(
            instance_data.base_folder / "ModOrganizer.ini"
        ).load_file()

        # then
        assert ini_data["General"]["gameName"] == game.display_name
        assert ini_data["General"]["gamePath"] == str(game_folder).replace("\\", "/")

    def test_install_mod(
        self,
        app_config: AppConfig,
        test_fs: FakeFilesystem,
        instance: Instance,
        qt_resources: None,
    ) -> None:
        """
        Tests `core.mod_manager.modorganizer.modorganizer.ModOrganizer.install_mod()`.
        """

        self.test_create_instance(test_fs, qt_resources)

        # given
        mo2 = ModOrganizer()
        test_instance_path = Path("E:\\Modding\\Test Instance")
        instance_data = MO2InstanceInfo(
            display_name="Test Instance",
            game=Game.get_game_by_id("skyrimse"),
            profile="Default",
            is_global=False,
            base_folder=test_instance_path,
            mods_folder=test_instance_path / "mods",
            profiles_folder=test_instance_path / "profiles",
            install_mo2=False,  # This is important for now as the download is not mocked, yet
        )
        dst_instance: Instance = mo2.load_instance(
            instance_data, app_config.modname_limit, FileBlacklist.get_files()
        )
        overwritten_mod: Mod = self.get_mod_by_name(
            "Obsidian Weathers and Seasons", instance
        )
        overwriting_mod: Mod = self.get_mod_by_name(
            "Obsidian Weathers and Seasons - German", instance
        )

        # when
        for mod in [overwritten_mod, overwriting_mod]:
            mo2.install_mod(
                mod,
                dst_instance,
                instance_data,
                file_redirects=mo2.get_actual_files(mod),
                use_hardlinks=True,
                replace=True,
                blacklist=FileBlacklist.get_files(),
            )
        mo2.finalize_migration(
            dst_instance, instance_data, order_matters=True, activate_new_instance=True
        )

        dst_instance = mo2.load_instance(
            instance_data, app_config.modname_limit, FileBlacklist.get_files()
        )
        migrated_overwritten_mod: Mod = self.get_mod_by_name(
            "Obsidian Weathers and Seasons", dst_instance
        )
        migrated_overwriting_mod: Mod = self.get_mod_by_name(
            "Obsidian Weathers and Seasons - German", dst_instance
        )

        # then
        assert migrated_overwritten_mod.metadata == overwritten_mod.metadata
        assert migrated_overwriting_mod.metadata == overwriting_mod.metadata
        assert migrated_overwritten_mod.mod_conflicts == [migrated_overwriting_mod]
        assert dst_instance.loadorder.index(
            migrated_overwritten_mod
        ) < dst_instance.loadorder.index(migrated_overwriting_mod)
        assert Utils.compare_path_list(
            migrated_overwritten_mod.files, overwritten_mod.files
        )
        assert Utils.compare_path_list(
            migrated_overwriting_mod.files, overwriting_mod.files
        )

    def test_install_mod_with_separator(
        self,
        app_config: AppConfig,
        test_fs: FakeFilesystem,
        instance: Instance,
        qt_resources: None,
    ) -> None:
        """
        Tests `core.mod_manager.modorganizer.modorganizer.ModOrganizer.install_mod()`
        with a separator mod.
        """

        self.test_create_instance(test_fs, qt_resources)

        # given
        mo2 = ModOrganizer()
        test_instance_path = Path("E:\\Modding\\Test Instance")
        instance_data = MO2InstanceInfo(
            display_name="Test Instance",
            game=Game.get_game_by_id("skyrimse"),
            profile="Default",
            is_global=False,
            base_folder=test_instance_path,
            mods_folder=test_instance_path / "mods",
            profiles_folder=test_instance_path / "profiles",
            install_mo2=False,  # This is important for now as the download is not mocked, yet
        )
        dst_instance: Instance = mo2.load_instance(
            instance_data, app_config.modname_limit, FileBlacklist.get_files()
        )
        separator_mod: Mod = self.get_mod_by_name("Test Mods", instance)

        # when
        mo2.install_mod(
            separator_mod,
            dst_instance,
            instance_data,
            file_redirects=mo2.get_actual_files(separator_mod),
            use_hardlinks=True,
            replace=True,
            blacklist=FileBlacklist.get_files(),
        )
        mo2.finalize_migration(
            dst_instance, instance_data, order_matters=True, activate_new_instance=True
        )

        dst_instance = mo2.load_instance(
            instance_data, app_config.modname_limit, FileBlacklist.get_files()
        )
        migrated_separator_mod: Mod = self.get_mod_by_name("Test Mods", dst_instance)

        # then
        assert migrated_separator_mod.mod_type == Mod.Type.Separator
