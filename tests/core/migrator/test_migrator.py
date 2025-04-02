"""
Copyright (c) Cutleast
"""

from pathlib import Path

from pyfakefs.fake_filesystem import FakeFilesystem

from core.instance.instance import Instance
from core.instance.mod import Mod
from core.migrator.migration_report import MigrationReport
from core.migrator.migrator import FileBlacklist, Migrator
from core.mod_manager.modorganizer.mo2_instance_info import MO2InstanceInfo
from core.mod_manager.modorganizer.modorganizer import ModOrganizer
from core.mod_manager.vortex.profile_info import ProfileInfo
from core.mod_manager.vortex.vortex import Vortex
from core.utilities.env_resolver import resolve
from tests.utils import Utils

from .._setup.mock_plyvel import MockPlyvelDB
from ..base_test import BaseTest


class TestMigrator(BaseTest):
    """
    Tests `core.migrator.migrator.Migrator`.
    """

    def test_migration_mo2_to_mo2(
        self,
        test_fs: FakeFilesystem,
        instance_info: MO2InstanceInfo,
        instance: Instance,
    ) -> None:
        """
        Tests `core.migrator.migrator.Migrator.migrate()` from MO2 to MO2.
        """

        # given
        mo2 = ModOrganizer()
        migrator = Migrator()
        instance_info.game.installdir = Path("E:\\Games\\Skyrim Special Edition")
        dst_path = Path("E:\\Modding\\Test Instance")
        dst_info = MO2InstanceInfo(
            display_name="Test Instance",
            game=instance_info.game,
            profile="Default",
            is_global=False,
            base_folder=dst_path,
            mods_folder=dst_path / "mods",
            profiles_folder=dst_path / "profiles",
            install_mo2=False,  # This is important for now as the download is not mocked, yet
        )

        # when
        report: MigrationReport = migrator.migrate(
            src_instance=instance,
            src_info=instance_info,
            dst_info=dst_info,
            src_mod_manager=mo2,
            dst_mod_manager=mo2,
            use_hardlinks=True,
            replace=True,
        )

        # then
        assert not report.has_errors

        # when
        migrated_instance: Instance = mo2.load_instance(
            dst_info, FileBlacklist.get_files()
        )

        # then
        self.assert_modlists_equal(migrated_instance.mods, instance.mods)
        assert len(migrated_instance.tools) == len(instance.tools)

    def test_migration_mo2_to_vortex(
        self,
        ready_vortex_db: MockPlyvelDB,
        test_fs: FakeFilesystem,
        instance_info: MO2InstanceInfo,
        instance: Instance,
    ) -> None:
        """
        Tests `core.migrator.migrator.Migrator.migrate()` from MO2 to Vortex.
        """

        appdata_path: Path = resolve(Path("%APPDATA%") / "Vortex")
        game_folder: Path = appdata_path / "skyrimse"
        game_folder.mkdir(parents=True, exist_ok=True)

        # given
        mo2 = ModOrganizer()
        vortex = Vortex()
        vortex.db_path.mkdir(parents=True, exist_ok=True)
        migrator = Migrator()
        instance_info.game.installdir = Path("E:\\Games\\Skyrim Special Edition")
        instance_info.game.installdir.mkdir(parents=True, exist_ok=True)
        dst_info = ProfileInfo(
            display_name="Test Instance",
            game=instance_info.game,
            id="1a2b3c4d",
        )

        # when
        report: MigrationReport = migrator.migrate(
            src_instance=instance,
            src_info=instance_info,
            dst_info=dst_info,
            src_mod_manager=mo2,
            dst_mod_manager=vortex,
            use_hardlinks=True,
            replace=True,
        )

        # then
        assert not report.has_errors

        # when
        migrated_profile_info = ProfileInfo(
            display_name="Test Instance (1a2b3c4d)",
            game=instance_info.game,
            id="1a2b3c4d",
        )
        migrated_instance: Instance = vortex.load_instance(
            migrated_profile_info, FileBlacklist.get_files()
        )

        # then
        self.assert_modlists_equal(
            migrated_instance.mods,
            instance.mods,
            exclude_separators=True,  # Vortex doesn't support separators and ignores them when migrating
        )
        assert len(migrated_instance.tools) == len(instance.tools)

    def assert_modlists_equal(
        self,
        modlist1: list[Mod],
        modlist2: list[Mod],
        check_files: bool = True,
        exclude_separators: bool = False,
    ) -> None:
        """
        Asserts that two mod lists are equal. Compares loadorder, metadata, enabled
        and files (if `check_files` is True).

        Args:
            modlist1 (list[Mod]): First mod list.
            modlist2 (list[Mod]): Second mod list.
            check_files (bool, optional):
                Whether to check the files of the mods. Defaults to True.
            exclude_separators (bool, optional):
                Whether to exclude separators from the comparison. Defaults to False.

        Raises:
            AssertionError: When the mod lists are not equal.
        """

        if exclude_separators:
            modlist1 = list(
                filter(lambda m: m.mod_type != Mod.Type.Separator, modlist1)
            )
            modlist2 = list(
                filter(lambda m: m.mod_type != Mod.Type.Separator, modlist2)
            )

        modnames1: list[str] = [mod.display_name for mod in modlist1]
        modnames2: list[str] = [mod.display_name for mod in modlist2]

        assert modnames1 == modnames2

        for mod1, mod2 in zip(modlist1, modlist2):
            assert mod1.metadata == mod2.metadata
            assert mod1.enabled == mod2.enabled
            assert mod1.mod_type == mod2.mod_type
            assert mod1.deploy_path == mod2.deploy_path
            assert list(map(lambda m: m.metadata, mod1.mod_conflicts)) == list(
                map(lambda m: m.metadata, mod2.mod_conflicts)
            )
            if check_files:
                assert Utils.compare_path_list(
                    list(
                        filter(  # Do not compare files on the blacklist
                            lambda f: str(f).lower() not in FileBlacklist.get_files(),
                            mod1.files,
                        )
                    ),
                    list(
                        filter(  # Do not compare files on the blacklist
                            lambda f: str(f).lower() not in FileBlacklist.get_files(),
                            mod2.files,
                        )
                    ),
                )
