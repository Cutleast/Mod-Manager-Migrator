"""
Copyright (c) Cutleast
"""

from pathlib import Path
from typing import Any

from pyfakefs.fake_filesystem import FakeFilesystem

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

    def test_parse_meta_ini(self, data_folder: Path, qt_resources: None) -> None:
        """
        Tests `core.mod_manager.modorganizer.modorganizer.ModOrganizer.__parse_meta_ini()`.
        """

        # given
        mo2 = ModOrganizer()
        test_meta_ini_path: Path = (
            data_folder / "mods" / "Metadata Test Mod" / "meta.ini"
        )

        # when
        metadata: Metadata = Utils.get_private_method(
            mo2, "parse_meta_ini", TestModOrganizer.parse_meta_ini_stub
        )(
            meta_ini_path=test_meta_ini_path,
            default_game=Game.get_game_by_id("skyrimse"),
        )

        # then
        assert metadata.mod_id == -1
        assert metadata.file_id is None
        assert metadata.version == ""
        assert metadata.file_name is None

    def test_load_instance(self, data_folder: Path, qt_resources: None) -> None:
        """
        Tests `core.mod_manager.modorganizer.modorganizer.ModOrganizer.load_instance()`.
        """

        # given
        mo2 = ModOrganizer()
        test_instance_path: Path = data_folder / "mod_instance"
        instance_data = MO2InstanceInfo(
            display_name="Test Instance",
            game=Game.get_game_by_id("skyrimse"),
            profile="Default",
            is_global=False,
            base_folder=test_instance_path,
            mods_folder=test_instance_path / "mods",
            profiles_folder=test_instance_path / "profiles",
        )

        # when
        instance: Instance = mo2.load_instance(instance_data, FileBlacklist.get_files())

        # then
        assert len(instance.mods) == 7

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

    def test_create_instance(self, fs: FakeFilesystem, qt_resources: None) -> None:
        """
        Tests `core.mod_manager.modorganizer.modorganizer.ModOrganizer.create_instance()`.
        """

        # given
        mo2 = ModOrganizer()
        game: Game = Game.get_game_by_id("skyrimse")
        game.installdir = Path("E:\\Games\\Skyrim Special Edition")
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
        instance: Instance = mo2.create_instance(instance_data)

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
        assert ini_data["General"]["gamePath"] == str(game.installdir).replace(
            "\\", "/"
        )

    def test_install_mod(
        self,
        data_folder: Path,
        instance: Instance,
        fs: FakeFilesystem,
        qt_resources: None,
    ) -> None:
        """
        Tests `core.mod_manager.modorganizer.modorganizer.ModOrganizer.install_mod()`.
        """

        self.test_create_instance(fs, qt_resources)
        fs.add_real_directory(data_folder)

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
            instance_data, FileBlacklist.get_files()
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
                use_hardlinks=True,
                replace=True,
                blacklist=FileBlacklist.get_files(),
            )
        mo2.finalize_migration(dst_instance, instance_data, order_matters=True)

        dst_instance = mo2.load_instance(instance_data, FileBlacklist.get_files())
        migrated_overwritten_mod: Mod = self.get_mod_by_name(
            "Obsidian Weathers and Seasons", dst_instance
        )
        migrated_overwriting_mod: Mod = self.get_mod_by_name(
            "Obsidian Weathers and Seasons - German", dst_instance
        )

        # then
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
        self, test_fs: FakeFilesystem, instance: Instance, qt_resources: None
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
            instance_data, FileBlacklist.get_files()
        )
        separator_mod: Mod = self.get_mod_by_name("Test Mods", instance)

        # when
        mo2.install_mod(
            separator_mod,
            dst_instance,
            instance_data,
            use_hardlinks=True,
            replace=True,
            blacklist=FileBlacklist.get_files(),
        )
        mo2.finalize_migration(dst_instance, instance_data, order_matters=True)

        dst_instance = mo2.load_instance(instance_data, FileBlacklist.get_files())
        migrated_separator_mod: Mod = self.get_mod_by_name("Test Mods", dst_instance)

        # then
        assert migrated_separator_mod.mod_type == Mod.Type.Separator
