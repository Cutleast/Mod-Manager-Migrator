"""
Copyright (c) Cutleast
"""

import logging
import os
import shutil
from abc import abstractmethod
from pathlib import Path
from typing import Optional, override

from PySide6.QtCore import QObject

from core.game.game import Game
from core.instance.instance import Instance
from core.instance.mod import Mod
from core.instance.tool import Tool
from core.utilities.logger import Logger
from core.utilities.scale import scale_value
from ui.widgets.loading_dialog import LoadingDialog

from .instance_info import InstanceInfo


class ModManager[I: InstanceInfo](QObject):
    """
    Abstract class for mod managers.
    """

    log: logging.Logger

    def __init__(self) -> None:
        super().__init__()

        self.log = logging.getLogger(self.__repr__())

    @staticmethod
    @abstractmethod
    def get_id() -> str:
        """
        Returns:
            str: The internal id of the mod manager.
        """

    @staticmethod
    @abstractmethod
    def get_display_name() -> str:
        """
        Returns:
            str: The display name of the mod manager.
        """

    @staticmethod
    @abstractmethod
    def get_icon_name() -> str:
        """
        Returns:
            str: The name of the icon resource of the mod manager.
        """

    @override
    def __hash__(self) -> int:
        return hash(self.get_id())

    @abstractmethod
    def get_instance_names(self, game: Game) -> list[str]:
        """
        Loads and returns a list of the names of all mod instances that are managed
        by this mod manager.

        Args:
            game (Game): The selected game.

        Returns:
            list[str]: The names of all mod instances.
        """

    @abstractmethod
    def load_instance(
        self,
        instance_data: I,
        modname_limit: int,
        file_blacklist: list[str] = [],
        game_folder: Optional[Path] = None,
        ldialog: Optional[LoadingDialog] = None,
    ) -> Instance:
        """
        Loads and returns the mod instance with the given name.

        Args:
            instance_data (I): The data of the mod instance.
            modname_limit (int): A character limit for mod names.
            file_blacklist (list[str], optional): A list of files to ignore.
            game_folder (Optional[Path], optional): The game folder of the instance.
            ldialog (Optional[LoadingDialog], optional):
                Optional loading dialog. Defaults to None.

        Raises:
            InstanceNotFoundError: If the mod instance does not exist.
            GameNotFoundError:
                If the game folder of the instance could not be found and is not
                specified.

        Returns:
            Instance: The mod instance with the given name.
        """

    @abstractmethod
    def _load_mods(
        self,
        instance_data: I,
        modname_limit: int,
        game_folder: Path,
        file_blacklist: list[str] = [],
        ldialog: Optional[LoadingDialog] = None,
    ) -> list[Mod]:
        """
        Loads and returns a list of mods for the given instance name.

        Args:
            instance_data (I): The data of the mod instance.
            modname_limit (int): A character limit for mod names.
            game_folder (Path): The game folder of the instance.
            file_blacklist (list[str], optional): A list of files to ignore.
            ldialog (Optional[LoadingDialog], optional):
                Optional loading dialog. Defaults to None.

        Returns:
            list[Mod]: The list of mods.
        """

    @abstractmethod
    def _load_tools(
        self,
        instance_data: I,
        mods: list[Mod],
        game_folder: Path,
        file_blacklist: list[str] = [],
        ldialog: Optional[LoadingDialog] = None,
    ) -> list[Tool]:
        """
        Loads and returns a list of tools for the given instance.

        Args:
            instance_data (I): The data of the mod instance.
            mods (list[Mod]): The list of already loaded mods.
            game_folder (Path): The game folder of the instance.
            file_blacklist (list[str], optional): A list of files to ignore.
            ldialog (Optional[LoadingDialog], optional):
                Optional loading dialog. Defaults to None.

        Returns:
            list[Tool]: The list of tools.
        """

    @staticmethod
    def _get_mod_for_path(
        path: Path, mods_by_folders: dict[Path, Mod]
    ) -> Optional[Mod]:
        """
        Returns the mod that contains the given path.

        Args:
            path (Path): The path.
            mods_by_folders (dict[Path, Mod]): The dict of mods by folders.

        Returns:
            Optional[Mod]: The mod that contains the given path or None.
        """

        for mod_path, mod in mods_by_folders.items():
            if path.is_relative_to(mod_path):
                return mod

    @staticmethod
    @Logger.timeit(logger_name="ModManager")
    def _index_modlist(
        mods: list[Mod], file_blacklist: list[str]
    ) -> dict[str, list[Mod]]:
        """
        Indexes all mod files and maps each file to a list of mods that contain it.

        Args:
            mods (list[Mod]): The list of mods.
            file_blacklist (list[str], optional): A list of file paths to ignore.

        Returns:
            dict[str, list[Mod]]: The indexed list of mods.
        """

        indexed_mods: dict[str, list[Mod]] = {}
        for mod in mods:
            for file in filter(
                lambda f: f.name.lower() not in file_blacklist, mod.files
            ):
                indexed_mods.setdefault(str(file).lower(), []).append(mod)

        return indexed_mods

    @staticmethod
    def _get_reversed_mod_conflicts(mods: list[Mod]) -> dict[Mod, list[Mod]]:
        """
        Returns a dict of mods that overwrite other mods.

        Args:
            mods (list[Mod]): The list of mods.

        Returns:
            dict[Mod, list[Mod]]: The dict of mods that overwrite other mods.
        """

        mod_overrides: dict[Mod, list[Mod]] = {}

        for mod in mods:
            if mod.mod_conflicts:
                for overwriting_mod in mod.mod_conflicts:
                    mod_overrides.setdefault(overwriting_mod, []).append(mod)

        return mod_overrides

    @staticmethod
    def get_actual_files(mod: Mod) -> dict[Path, Path]:
        """
        Returns a dict of real file paths to actual file paths.
        Only contains files where the real path differs from the actual path.

        For example:
            `scripts\\_wetskyuiconfig.pex.mohidden` -> `scripts\\_wetskyuiconfig.pex`

        Args:
            mod (Mod): The mod.

        Returns:
            dict[Path, Path]: The dict of real file paths to actual file paths.
        """

        return {}

    @abstractmethod
    def create_instance(
        self,
        instance_data: I,
        game_folder: Path,
        ldialog: Optional[LoadingDialog] = None,
    ) -> Instance:
        """
        Creates an instance in this mod manager.

        Args:
            instance_data (Instance_data): The customized instance data to create.
            game_folder (Path): The game folder to use for the created instance.
            ldialog (Optional[LoadingDialog], optional):
                Optional loading dialog. Defaults to None.

        Returns:
            Instance: The created instance.
        """

    @abstractmethod
    def install_mod(
        self,
        mod: Mod,
        instance: Instance,
        instance_data: I,
        file_redirects: dict[Path, Path],
        use_hardlinks: bool,
        replace: bool,
        blacklist: list[str] = [],
        ldialog: Optional[LoadingDialog] = None,
    ) -> None:
        """
        Installs a mod to the current instance.

        Args:
            mod (Mod): The mod to install.
            instance (Instance): The instance to install the mod to.
            instance_data (I): The data of the instance above.
            file_redirects (dict[Path, Path]): A dict of file redirects.
            use_hardlinks (bool): Whether to use hardlinks if possible.
            replace (bool): Whether to replace existing files.
            blacklist (list[str], optional): A list of files to not migrate.
            ldialog (Optional[LoadingDialog], optional):
                Optional loading dialog. Defaults to None.
        """

    @abstractmethod
    def add_tool(
        self,
        tool: Tool,
        instance: Instance,
        instance_data: I,
        use_hardlinks: bool,
        replace: bool,
        blacklist: list[str] = [],
        ldialog: Optional[LoadingDialog] = None,
    ) -> None:
        """
        Adds a tool to the mod manager.

        Args:
            tool (Tool): The tool to add.
            instance (Instance): The instance to add the tool to.
            instance_data (I): The data of the instance above.
            use_hardlinks (bool): Whether to use hardlinks if possible.
            replace (bool): Whether to replace existing files.
            blacklist (list[str], optional): A list of files to not migrate.
            ldialog (Optional[LoadingDialog], optional):
                Optional loading dialog. Defaults to None.
        """

    def _migrate_mod_files(
        self,
        mod: Mod,
        mod_folder: Path,
        file_redirects: dict[Path, Path],
        use_hardlinks: bool,
        replace: bool,
        blacklist: list[str] = [],
        ldialog: Optional[LoadingDialog] = None,
    ) -> None:
        """
        Migrates the files of a mod to the destination path.

        Args:
            mod (Mod): The mod to migrate.
            mod_folder (Path): The destination path.
            use_hardlinks (bool): Whether to use hardlinks if possible.
            file_redirects (dict[Path, Path]): A dict of file redirects.
            replace (bool): Whether to replace existing files.
            blacklist (list[str], optional): A list of files to not migrate.
            ldialog (Optional[LoadingDialog], optional):
                Optional loading dialog. Defaults to None.
        """

        for f, file in enumerate(mod.files):
            if file.name.lower() in blacklist:
                self.log.info(
                    f"Skipped file due to configured blacklist: {file.name!r}"
                )
                continue

            src_path: Path = mod.path / file
            dst_path: Path = mod_folder / file_redirects.get(file, file)

            if ldialog:
                ldialog.updateProgress(
                    text2=f"{mod.display_name} ({f}/{len(mod.files)})",
                    value2=f,
                    max2=len(mod.files),
                    show3=True,
                    text3=f"{file.name} ({scale_value(src_path.stat().st_size)})",
                )

            if src_path == dst_path:
                self.log.warning(f"Skipped file due to same path: {str(src_path)!r}")
                continue

            dst_path.parent.mkdir(parents=True, exist_ok=True)

            if dst_path.is_file() and replace:
                dst_path.unlink()
                self.log.warning(f"Deleted existing file: {str(dst_path)!r}")
            elif not replace:
                self.log.info(f"Skipped existing file: {str(dst_path)!r}")
                continue

            if src_path.drive.lower() == dst_path.drive.lower() and use_hardlinks:
                os.link(src_path, dst_path)
            else:
                shutil.copyfile(src_path, dst_path)

    def get_ini_files(self, instance: Instance, instance_data: I) -> list[Path]:
        """
        Returns a list of ini files to migrate.

        Args:
            instance (Instance): The instance.
            instance_data (I): The data of the instance.

        Returns:
            list[Path]: The list of ini files.
        """

        ini_filenames: list[Path] = instance_data.game.inifiles
        ini_dir: Path = self.get_ini_dir(instance_data, instance.separate_ini_files)

        return [(ini_dir / file) for file in ini_filenames]

    def get_ini_dir(self, instance_data: I, separate_ini_files: bool) -> Path:
        """
        Returns path to folder for INI files, either game's INI folder or
        instance's INI folder.

        Args:
            instance_data (I): The data of the instance.
            separate_ini_files (bool): Whether to use separate INI folders.

        Returns:
            Path: The path to the INI folder.
        """

        if separate_ini_files:
            return self.get_instance_ini_dir(instance_data)

        return instance_data.game.inidir

    @abstractmethod
    def get_instance_ini_dir(self, instance_data: I) -> Path:
        """
        Returns the path to the instance's INI folder.

        Args:
            instance_data (I): The data of the instance.

        Returns:
            Path: The path to the instance's INI folder.
        """

    def migrate_ini_files(
        self,
        files: list[Path],
        instance_data: I,
        separate_ini_files: bool,
        use_hardlinks: bool,
        replace: bool,
        ldialog: Optional[LoadingDialog] = None,
    ) -> None:
        """
        Migrates the specified INI files to the destination path.

        Args:
            files (list[Path]): The INI files to migrate.
            instance_data (I): The data of the instance.
            separate_ini_files (bool): Whether to use separate INI folders.
            use_hardlinks (bool): Whether to use hardlinks if possible.
            replace (bool): Whether to replace existing files.
            ldialog (Optional[LoadingDialog], optional):
                Optional loading dialog. Defaults to None.
        """

        dest_folder: Path = self.get_ini_dir(instance_data, separate_ini_files)

        for f, file in enumerate(files):
            dst_path: Path = dest_folder / file.name

            self.log.info(
                f"Migrating ini file {file.name!r} from "
                f"{str(file.parent)!r} to {str(dest_folder)!r}..."
            )
            if ldialog:
                ldialog.updateProgress(
                    text2=f"{file.name} ({f}/{len(files)})",
                    value2=f,
                    max2=len(files),
                    show3=True,
                    text3=f"{file.name} ({scale_value(file.stat().st_size)})",
                )

            dest_folder.mkdir(parents=True, exist_ok=True)

            if dst_path.is_file() and replace:
                dst_path.unlink()
                self.log.warning(f"Deleted existing file: {str(dst_path)!r}")
            elif not replace:
                self.log.info(f"Skipped existing file: {str(dst_path)!r}")
                continue

            if file.drive.lower() == dst_path.drive.lower() and use_hardlinks:
                os.link(file, dst_path)
            else:
                shutil.copyfile(file, dst_path)

    def get_additional_files(self, instance_data: I) -> list[Path]:
        """
        Returns a list of additional files to migrate.

        Args:
            instance_data (I): The data of the instance.

        Returns:
            list[Path]: The list of additional files.
        """

        file_names: list[str] = instance_data.game.additional_files
        add_folder: Path = self.get_additional_files_folder(instance_data)

        return [
            add_folder / file_name
            for file_name in file_names
            if (add_folder / file_name).is_file()
        ]

    def migrate_additional_files(
        self,
        files: list[Path],
        instance_data: I,
        use_hardlinks: bool,
        replace: bool,
        ldialog: Optional[LoadingDialog] = None,
    ) -> None:
        """
        Migrates the specified additional files to the specified destination path.

        Args:
            files (list[Path]): The list of additional files.
            instance_data (I): The data of the instance.
            use_hardlinks (bool): Whether to use hardlinks if possible.
            replace (bool): Whether to replace existing files.
            ldialog (Optional[LoadingDialog], optional):
                Optional loading dialog. Defaults to None.
        """

        dest_folder: Path = self.get_additional_files_folder(instance_data)

        for f, file in enumerate(files):
            dst_path: Path = dest_folder / file.name

            self.log.info(
                f"Migrating additional file {file.name!r} from "
                f"{str(file.parent)!r} to {str(dest_folder)!r}..."
            )
            if ldialog:
                ldialog.updateProgress(
                    text2=f"{file.name} ({f}/{len(files)})",
                    value2=f,
                    max2=len(files),
                    show3=True,
                    text3=f"{file.name} ({scale_value(file.stat().st_size)})",
                )

            dest_folder.mkdir(parents=True, exist_ok=True)

            if dst_path.is_file() and replace:
                dst_path.unlink()
                self.log.warning(f"Deleted existing file: {str(dst_path)!r}")
            elif not replace:
                self.log.info(f"Skipped existing file: {str(dst_path)!r}")
                continue

            if file.drive.lower() == dst_path.drive.lower() and use_hardlinks:
                os.link(file, dst_path)
            else:
                shutil.copyfile(file, dst_path)

    @abstractmethod
    def get_additional_files_folder(self, instance_data: I) -> Path:
        """
        Gets the path for the additional files of the specified instance.

        Args:
            instance_data (I): The data of the instance.

        Returns:
            Path: The path for the additional files.
        """

    def prepare_migration(self, instance_data: I) -> None:
        """
        Prepares the migration process. Runs pre-migration checks, if necessary
        and raises an Exception if there are issues or potential error sources.

        Args:
            instance_data (I): The data of the instance.

        Raises:
            PreMigrationCheckFailedError: when the pre-migration check fails.
        """

    def finalize_migration(
        self,
        migrated_instance: Instance,
        migrated_instance_data: I,
        order_matters: bool,
        activate_new_instance: bool,
    ) -> None:
        """
        Finalizes the migration process.

        Args:
            migrated_instance (Instance): The migrated instance.
            migrated_instance_data (I): The data of the migrated instance.
            order_matters (bool):
                Whether the mods of the source instance have a fixed order.
            activate_new_instance (bool):
                Whether to activate the new instance (if supported by the mod manager).
        """

    def get_completed_message(self, migrated_instance_data: I) -> str:
        """
        Get text to display to the user after the migration is completed.

        Args:
            migrated_instance_data (I): The data of the migrated instance.

        Returns:
            str: Text to display to the user.
        """

        return ""

    @abstractmethod
    def get_mods_path(self, instance_data: I) -> Path:
        """
        Returns the path to the specified instance's mods folder.

        Args:
            instance_data (I): The data of the instance.

        Returns:
            Path: The path to the mods folder.
        """

    @abstractmethod
    def is_instance_existing(self, instance_data: I) -> bool:
        """
        Checks if the specified instance exists.

        Args:
            instance_data (I): The data of the instance.

        Returns:
            bool: Whether the instance exists.
        """
