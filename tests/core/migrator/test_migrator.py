"""
Copyright (c) Cutleast
"""

from pathlib import Path

from pyfakefs.fake_filesystem import FakeFilesystem

from core.config.app_config import AppConfig
from core.instance.instance import Instance
from core.instance.mod import Mod
from core.migrator.migration_report import MigrationReport
from core.migrator.migrator import FileBlacklist, Migrator
from core.mod_manager.mod_manager import ModManager
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
        app_config: AppConfig,
        test_fs: FakeFilesystem,
        mo2_instance_info: MO2InstanceInfo,
        instance: Instance,
    ) -> None:
        """
        Tests `core.migrator.migrator.Migrator.migrate()` from MO2 to MO2.
        """

        # given
        mo2 = ModOrganizer()
        migrator = Migrator()
        mo2_instance_info.game.installdir = Path(
            "E:\\SteamLibrary\\Skyrim Special Edition"
        )
        dst_path = Path("E:\\Modding\\Test Instance")
        dst_info = MO2InstanceInfo(
            display_name="Test Instance",
            game=mo2_instance_info.game,
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
            src_info=mo2_instance_info,
            dst_info=dst_info,
            src_mod_manager=mo2,
            dst_mod_manager=mo2,
            use_hardlinks=True,
            replace=True,
            modname_limit=app_config.modname_limit,
            activate_new_instance=app_config.activate_new_instance,
        )

        # then
        assert not report.has_errors

        # when
        migrated_instance: Instance = mo2.load_instance(
            dst_info, app_config.modname_limit, FileBlacklist.get_files()
        )

        # then
        self.assert_modlists_equal(migrated_instance.mods, instance.mods)
        assert len(migrated_instance.tools) == len(instance.tools)

    def test_migration_mo2_to_vortex(
        self,
        app_config: AppConfig,
        ready_vortex_db: MockPlyvelDB,
        test_fs: FakeFilesystem,
        mo2_instance_info: MO2InstanceInfo,
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
        mo2_instance_info.game.installdir = Path(
            "E:\\SteamLibrary\\Skyrim Special Edition"
        )
        mo2_instance_info.game.installdir.mkdir(parents=True, exist_ok=True)
        dst_info = ProfileInfo(
            display_name="Test Instance",
            game=mo2_instance_info.game,
            id="5e6f7g8h9j",
        )

        # when
        report: MigrationReport = migrator.migrate(
            src_instance=instance,
            src_info=mo2_instance_info,
            dst_info=dst_info,
            src_mod_manager=mo2,
            dst_mod_manager=vortex,
            use_hardlinks=True,
            replace=True,
            modname_limit=app_config.modname_limit,
            activate_new_instance=True,
        )

        # then
        assert not report.has_errors
        assert (
            ready_vortex_db.get(b"settings###profiles###activeProfileId")
            == b'"5e6f7g8h9j"'
        )
        assert (
            ready_vortex_db.get(b"settings###profiles###lastActiveProfile###skyrimse")
            == b'"5e6f7g8h9j"'
        )

        # when
        migrated_profile_info = ProfileInfo(
            display_name="Test Instance (5e6f7g8h9j)",
            game=mo2_instance_info.game,
            id="5e6f7g8h9j",
        )
        migrated_instance: Instance = vortex.load_instance(
            migrated_profile_info, app_config.modname_limit, FileBlacklist.get_files()
        )

        # then
        self.assert_modlists_equal(
            migrated_instance.mods,
            instance.mods,
            self.__get_file_redirects(migrated_instance.mods, vortex),
            self.__get_file_redirects(instance.mods, mo2),
            exclude_separators=True,  # Vortex doesn't support separators and ignores them when migrating
        )
        assert len(migrated_instance.tools) == len(instance.tools)

    def test_migration_to_vortex_without_activating_profile(
        self,
        app_config: AppConfig,
        ready_vortex_db: MockPlyvelDB,
        test_fs: FakeFilesystem,
        mo2_instance_info: MO2InstanceInfo,
        instance: Instance,
    ) -> None:
        """
        Tests `core.migrator.migrator.Migrator.migrate()` to Vortex without activating
        the new profile.
        """

        appdata_path: Path = resolve(Path("%APPDATA%") / "Vortex")
        game_folder: Path = appdata_path / "skyrimse"
        game_folder.mkdir(parents=True, exist_ok=True)

        # given
        mo2 = ModOrganizer()
        vortex = Vortex()
        vortex.db_path.mkdir(parents=True, exist_ok=True)
        migrator = Migrator()
        mo2_instance_info.game.installdir = Path(
            "E:\\SteamLibrary\\Skyrim Special Edition"
        )
        mo2_instance_info.game.installdir.mkdir(parents=True, exist_ok=True)
        dst_info = ProfileInfo(
            display_name="Test Instance",
            game=mo2_instance_info.game,
            id="5e6f7g8h9j",
        )

        # when
        report: MigrationReport = migrator.migrate(
            src_instance=instance,
            src_info=mo2_instance_info,
            dst_info=dst_info,
            src_mod_manager=mo2,
            dst_mod_manager=vortex,
            use_hardlinks=True,
            replace=True,
            modname_limit=app_config.modname_limit,
            activate_new_instance=False,
        )

        # then
        assert not report.has_errors

        # when
        assert (
            ready_vortex_db.get(b"settings###profiles###activeProfileId")
            != b'"5e6f7g8h9j"'
        )
        assert (
            ready_vortex_db.get(b"settings###profiles###lastActiveProfile###skyrimse")
            != b'"5e6f7g8h9j"'
        )

    def test_migration_vortex_to_mo2(
        self,
        data_folder: Path,
        app_config: AppConfig,
        full_vortex_db: MockPlyvelDB,
        test_fs: FakeFilesystem,
        vortex_profile_info: ProfileInfo,
    ) -> None:
        """
        Tests `core.migrator.migrator.Migrator.migrate()` from Vortex to MO2.
        """

        test_fs.add_real_directory(
            data_folder / "skyrimse",
            target_path=resolve(Path("%APPDATA%")) / "Vortex" / "skyrimse",
        )

        # given
        vortex = Vortex()
        vortex.db_path.mkdir(parents=True, exist_ok=True)
        mo2 = ModOrganizer()
        migrator = Migrator()
        vortex_profile_info.game.installdir = Path(
            "E:\\SteamLibrary\\Skyrim Special Edition"
        )
        vortex_profile_info.game.installdir.mkdir(parents=True, exist_ok=True)
        dst_path = Path("E:\\Modding\\Test Instance")
        dst_info = MO2InstanceInfo(
            display_name="Test Instance",
            game=vortex_profile_info.game,
            profile="Default",
            is_global=False,
            base_folder=dst_path,
            mods_folder=dst_path / "mods",
            profiles_folder=dst_path / "profiles",
            install_mo2=False,  # This is important for now as the download is not mocked, yet
        )
        src_instance = vortex.load_instance(
            vortex_profile_info, app_config.modname_limit, FileBlacklist.get_files()
        )

        # when
        report: MigrationReport = migrator.migrate(
            src_instance=src_instance,
            src_info=vortex_profile_info,
            dst_info=dst_info,
            src_mod_manager=vortex,
            dst_mod_manager=mo2,
            use_hardlinks=True,
            replace=True,
            modname_limit=app_config.modname_limit,
            activate_new_instance=app_config.activate_new_instance,
        )

        # then
        assert not report.has_errors

        # when
        migrated_instance: Instance = mo2.load_instance(
            dst_info, app_config.modname_limit, FileBlacklist.get_files()
        )

        # then
        self.assert_modlists_equal(
            migrated_instance.mods,
            src_instance.loadorder,
            self.__get_file_redirects(migrated_instance.mods, mo2),
            self.__get_file_redirects(src_instance.mods, vortex),
        )
        assert len(migrated_instance.tools) == len(src_instance.tools)

    def test_migration_vortex_to_vortex(
        self,
        data_folder: Path,
        app_config: AppConfig,
        full_vortex_db: MockPlyvelDB,
        test_fs: FakeFilesystem,
        vortex_profile_info: ProfileInfo,
    ) -> None:
        """
        Tests `core.migrator.migrator.Migrator.migrate()` from Vortex to Vortex.
        """

        test_fs.add_real_directory(
            data_folder / "skyrimse",
            read_only=False,
            target_path=resolve(Path("%APPDATA%")) / "Vortex" / "skyrimse",
        )

        # given
        vortex = Vortex()
        vortex.db_path.mkdir(parents=True, exist_ok=True)
        migrator = Migrator()
        vortex_profile_info.game.installdir = Path(
            "E:\\SteamLibrary\\Skyrim Special Edition"
        )
        vortex_profile_info.game.installdir.mkdir(parents=True, exist_ok=True)
        dst_info = ProfileInfo(
            display_name="Test Instance",
            game=vortex_profile_info.game,
            id="5e6f7g8h9j",
        )
        src_instance = vortex.load_instance(
            vortex_profile_info, app_config.modname_limit, FileBlacklist.get_files()
        )

        # when
        report: MigrationReport = migrator.migrate(
            src_instance=src_instance,
            src_info=vortex_profile_info,
            dst_info=dst_info,
            src_mod_manager=vortex,
            dst_mod_manager=vortex,
            use_hardlinks=True,
            replace=True,
            modname_limit=app_config.modname_limit,
            activate_new_instance=True,
        )

        # then
        assert not report.has_errors
        assert (
            full_vortex_db.get(b"settings###profiles###activeProfileId")
            == b'"5e6f7g8h9j"'
        )
        assert (
            full_vortex_db.get(b"settings###profiles###lastActiveProfile###skyrimse")
            == b'"5e6f7g8h9j"'
        )

        # when
        migrated_profile_info = ProfileInfo(
            display_name="Test Instance (5e6f7g8h9j)",
            game=dst_info.game,
            id="5e6f7g8h9j",
        )
        migrated_instance: Instance = vortex.load_instance(
            migrated_profile_info, app_config.modname_limit, FileBlacklist.get_files()
        )

        # then
        self.assert_modlists_equal(migrated_instance.loadorder, src_instance.loadorder)
        assert len(migrated_instance.tools) == len(src_instance.tools)

    def assert_modlists_equal(
        self,
        modlist1: list[Mod],
        modlist2: list[Mod],
        file_redirects1: dict[Mod, dict[Path, Path]] = {},
        file_redirects2: dict[Mod, dict[Path, Path]] = {},
        check_files: bool = True,
        exclude_separators: bool = False,
    ) -> None:
        """
        Asserts that two mod lists are equal. Compares loadorder, metadata, enabled
        and files (if `check_files` is True).

        Args:
            modlist1 (list[Mod]): First mod list.
            modlist2 (list[Mod]): Second mod list.
            file_redirects1 (dict[Mod, dict[Path, Path]], optional):
                File redirects for the first mod list. Defaults to {}.
            file_redirects2 (dict[Mod, dict[Path, Path]], optional):
                File redirects for the second mod list. Defaults to {}.
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
            redirects1: dict[Path, Path] = file_redirects1.get(mod1, {})
            redirects2: dict[Path, Path] = file_redirects2.get(mod2, {})
            assert mod1.metadata == mod2.metadata
            assert mod1.enabled == mod2.enabled
            assert mod1.mod_type == mod2.mod_type
            assert mod1.deploy_path == mod2.deploy_path
            assert list(map(lambda m: m.metadata, mod1.mod_conflicts)) == list(
                map(lambda m: m.metadata, mod2.mod_conflicts)
            )
            assert {f: m.metadata for f, m in mod1.file_conflicts.items()} == {
                f: m.metadata for f, m in mod2.file_conflicts.items()
            }
            if check_files:
                assert Utils.compare_path_list(
                    list(
                        filter(  # Do not check special files
                            lambda f: str(f).lower() not in FileBlacklist.get_files()
                            and str(f) not in mod1.file_conflicts
                            and f not in redirects1
                            and f not in redirects2,
                            mod1.files,
                        )
                    ),
                    list(
                        filter(  # Do not check special files
                            lambda f: str(f).lower() not in FileBlacklist.get_files()
                            and str(f) not in mod2.file_conflicts
                            and f not in redirects2
                            and f not in redirects1,
                            mod2.files,
                        )
                    ),
                )

    def __get_file_redirects(
        self, mods: list[Mod], src_mod_manager: ModManager
    ) -> dict[Mod, dict[Path, Path]]:
        file_redirects: dict[Mod, dict[Path, Path]] = {}
        for mod in mods:
            redirects: dict[Path, Path] = src_mod_manager.get_actual_files(mod)

            if redirects:
                file_redirects[mod] = redirects

        return file_redirects
