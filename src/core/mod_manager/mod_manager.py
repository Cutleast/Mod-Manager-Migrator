"""
Copyright (c) Cutleast
"""

import logging
import os
import shutil
from abc import abstractmethod
from pathlib import Path
from typing import Optional

from PySide6.QtCore import QObject

from core.game.game import Game
from core.instance.instance import Instance
from core.instance.mod import Mod
from core.instance.tool import Tool
from core.utilities.scale import scale_value
from ui.widgets.loading_dialog import LoadingDialog

from .instance_info import InstanceInfo


class ModManager(QObject):
    """
    Abstract class for mod managers.
    """

    display_name: str
    """
    The name of the mod manager.
    """

    id: str
    """
    The internal id of the mod manager.
    """

    icon_name: str
    """
    The name of the icon resource of the mod manager.
    """

    log: logging.Logger

    def __init__(self) -> None:
        super().__init__()

        self.log = logging.getLogger(self.__repr__())

    def __hash__(self) -> int:
        return hash(self.id)

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
        self, instance_data: InstanceInfo, ldialog: Optional[LoadingDialog] = None
    ) -> Instance:
        """
        Loads and returns the mod instance with the given name.

        Args:
            instance_data (InstanceData): The data of the mod instance.
            ldialog (Optional[LoadingDialog], optional):
                Optional loading dialog. Defaults to None.

        Returns:
            Instance: The mod instance with the given name.
        """

    @abstractmethod
    def _load_mods(
        self, instance_data: InstanceInfo, ldialog: Optional[LoadingDialog] = None
    ) -> list[Mod]:
        """
        Loads and returns a list of mods for the given instance name.

        Args:
            instance_data (InstanceData): The data of the mod instance.
            ldialog (Optional[LoadingDialog], optional):
                Optional loading dialog. Defaults to None.

        Returns:
            list[Mod]: The list of mods.
        """

    @abstractmethod
    def _load_tools(
        self, instance_data: InstanceInfo, ldialog: Optional[LoadingDialog] = None
    ) -> list[Tool]:
        """
        Loads and returns a list of tools for the given instance.

        Args:
            instance_data (InstanceData): The data of the mod instance.
            ldialog (Optional[LoadingDialog], optional):
                Optional loading dialog. Defaults to None.

        Returns:
            list[Tool]: The list of tools.
        """

    @abstractmethod
    def create_instance(
        self, instance_data: InstanceInfo, ldialog: Optional[LoadingDialog] = None
    ) -> Instance:
        """
        Creates an instance in this mod manager.

        Args:
            instance_data (Instance_data): The customized instance data to create.
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
        instance_data: InstanceInfo,
        use_hardlinks: bool,
        replace: bool,
        ldialog: Optional[LoadingDialog] = None,
    ) -> None:
        """
        Installs a mod to the current instance.

        Args:
            mod (Mod): The mod to install.
            instance (Instance): The instance to install the mod to.
            instance_data (InstanceData): The data of the instance above.
            use_hardlinks (bool): Whether to use hardlinks if possible.
            replace (bool): Whether to replace existing files.
            ldialog (Optional[LoadingDialog], optional):
                Optional loading dialog. Defaults to None.
        """

    @abstractmethod
    def add_tool(
        self,
        tool: Tool,
        instance: Instance,
        instance_data: InstanceInfo,
        use_hardlinks: bool,
        replace: bool,
        ldialog: Optional[LoadingDialog] = None,
    ) -> None:
        """
        Adds a tool to the mod manager.

        Args:
            tool (Tool): The tool to add.
            instance (Instance): The instance to add the tool to.
            instance_data (InstanceData): The data of the instance above.
            use_hardlinks (bool): Whether to use hardlinks if possible.
            replace (bool): Whether to replace existing files.
            ldialog (Optional[LoadingDialog], optional):
                Optional loading dialog. Defaults to None.
        """

    def _migrate_mod_files(
        self,
        mod: Mod,
        mod_folder: Path,
        use_hardlinks: bool,
        replace: bool,
        ldialog: Optional[LoadingDialog] = None,
    ) -> None:
        """
        Migrates the files of a mod to the destination path.

        Args:
            mod (Mod): The mod to migrate.
            mod_folder (Path): The destination path.
            use_hardlinks (bool): Whether to use hardlinks if possible.
            replace (bool): Whether to replace existing files.
            ldialog (Optional[LoadingDialog], optional):
                Optional loading dialog. Defaults to None.
        """

        for f, file in enumerate(mod.files):
            src_path: Path = mod.path / file
            dst_path: Path = mod_folder / file

            if ldialog:
                ldialog.updateProgress(
                    text2=f"{mod.display_name} ({f}/{len(mod.files)})",
                    value2=f,
                    max2=len(mod.files),
                    show3=True,
                    text3=f"{file.name} ({scale_value(src_path.stat().st_size)})",
                )

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

    def get_additional_files(self, instance_data: InstanceInfo) -> list[Path]:
        """
        Returns a list of additional files to migrate.

        Args:
            instance_data (InstanceInfo): The data of the instance.

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
        instance_data: InstanceInfo,
        use_hardlinks: bool,
        replace: bool,
        ldialog: Optional[LoadingDialog] = None,
    ) -> None:
        """
        Migrates the specified additional files to the specified destination path.

        Args:
            files (list[Path]): The list of additional files.
            instance_data (InstanceInfo): The data of the instance.
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
    def get_additional_files_folder(self, instance_data: InstanceInfo) -> Path:
        """
        Gets the path for the additional files of the specified instance.

        Args:
            instance_data (InstanceInfo): The data of the instance.

        Returns:
            Path: The path for the additional files.
        """

    def finalize_migration(
        self, migrated_instance: Instance, migrated_instance_data: InstanceInfo
    ) -> None:
        """
        Finalizes the migration process.

        Args:
            migrated_instance (Instance): The migrated instance.
            migrated_instance_data (InstanceInfo): The data of the migrated instance.
        """

    def get_completed_message(self, migrated_instance_data: InstanceInfo) -> str:
        """
        Get text to display to the user after the migration is completed.

        Args:
            migrated_instance_data (InstanceData): The data of the migrated instance.

        Returns:
            str: Text to display to the user.
        """

        return self.tr("Migration completed successfully!")

    @abstractmethod
    def check_destination_disk_space(
        self, dst_info: InstanceInfo, src_size: int
    ) -> None:
        """
        Checks if the disk for the destination instance has enough space.

        Raises:
            NotEnoughSpaceError: when the disk has not enough space.

        Args:
            dst_info (InstanceInfo): The data of the destination instance.
            src_size (int): Size of the source instance in bytes.
        """
