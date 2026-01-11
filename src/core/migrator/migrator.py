"""
Copyright (c) Cutleast
"""

import logging
from pathlib import Path
from typing import Optional, cast

from cutleast_core_lib.core.utilities.logger import Logger
from cutleast_core_lib.core.utilities.scale import scale_value
from cutleast_core_lib.ui.widgets.loading_dialog import LoadingDialog
from mod_manager_lib.core.instance.instance import Instance
from mod_manager_lib.core.instance.mod import Mod
from mod_manager_lib.core.instance.tool import Tool
from mod_manager_lib.core.mod_manager.exceptions import InstanceNotFoundError
from mod_manager_lib.core.mod_manager.instance_info import InstanceInfo
from mod_manager_lib.core.mod_manager.mod_manager import ModManager
from mod_manager_lib.core.mod_manager.mod_manager_api import ModManagerApi
from mod_manager_lib.core.mod_manager.modorganizer.mo2_instance_info import (
    MO2InstanceInfo,
)
from mod_manager_lib.core.mod_manager.modorganizer.modorganizer import ModOrganizer
from mod_manager_lib.core.mod_manager.vortex.vortex import Vortex
from PySide6.QtCore import QObject

from core.utilities.exceptions import (
    NotEnoughSpaceError,
    SameModsLocationDiffManagerError,
    SameSourceDestinationError,
)
from core.utilities.filesystem import get_free_disk_space

from .file_blacklist import FileBlacklist
from .migration_report import MigrationReport


class Migrator(QObject):
    """
    Class that handles the migration process.
    """

    log: logging.Logger = logging.getLogger("Migrator")

    def migrate[S: InstanceInfo, D: InstanceInfo](
        self,
        src_instance: Instance,
        src_info: S,
        dst_info: D,
        src_mod_manager: ModManagerApi[S],
        dst_mod_manager: ModManagerApi[D],
        use_hardlinks: bool,
        replace: bool,
        modname_limit: int,
        activate_new_instance: bool,
        included_tools: list[Tool],
        ldialog: Optional[LoadingDialog] = None,
    ) -> MigrationReport:
        """
        Migrates an instance from one mod manager to another.

        Args:
            src_instance (Instance): Source mod instance.
            src_info (S): Information about the source mod instance.
            dst_info (D): Information about the destination mod instance.
            src_mod_manager (ModManager[S]): Source mod manager.
            dst_mod_manager (ModManager[D]): Destination mod manager.
            use_hardlinks (bool): Whether to use hardlinks if possible.
            replace (bool): Whether to replace existing files.
            modname_limit (int): A character limit for mod names.
            activate_new_instance (bool): Whether to activate the new instance.
            included_tools (list[Tool]): A list of tools to migrate.
            ldialog (Optional[LoadingDialog], optional):
                Optional loading dialog. Defaults to None.

        Raises:
            GameNotFoundError:
                When the game folder could not be retrieved from the source instance.
            SameSourceDestinationError:
                When the source and destination instances are the same.
            NotEnoughSpaceError:
                When the destination disk has not enough space.

        Returns:
            MigrationReport: A report containing migration errors.
        """

        if src_info == dst_info:
            raise SameSourceDestinationError

        self.log.info(
            f"Migrating instance {src_info.display_name!r} from "
            f"{src_mod_manager.get_display_name()} to "
            f"{dst_mod_manager.get_display_name()}..."
        )

        report = MigrationReport()

        self.log.info("Source instance info:")
        Logger.log_str_dict(self.log, src_info.__dict__)
        self.log.info(f"Source size: {scale_value(src_instance.size)}")
        self.log.info(f"Source order matters: {src_instance.order_matters}")

        self.log.info("Destination instance info:")
        Logger.log_str_dict(self.log, dst_info.__dict__)

        self.log.info(f"Mods: {len(src_instance.mods)}")
        self.log.info(f"Tools: {len(src_instance.tools)}")
        self.log.info(f"Game folder: {src_instance.game_folder}")
        self.log.info(f"Use hardlinks: {use_hardlinks}")
        self.log.info(f"Replace existing files: {replace}")
        self.log.info(f"Separate ini files: {src_instance.separate_ini_files}")
        self.log.info(f"Separate save games: {src_instance.separate_save_games}")
        self.log.info(f"Activate new instance: {activate_new_instance}")

        blacklist: list[str] = FileBlacklist.get_files()
        self.log.info(f"File blacklist: {', '.join(blacklist)}")

        src_mods_path: Path = src_mod_manager.get_mods_path(src_info)
        dst_mods_path: Path = dst_mod_manager.get_mods_path(dst_info)
        src_drive: str = src_mods_path.drive
        dst_drive: str = dst_mods_path.drive

        self.log.info(f"Source mods path: {src_mods_path}")
        self.log.info(f"Destination mods path: {dst_mods_path}")

        if (
            src_mods_path == dst_mods_path
            and src_mod_manager.get_id() != dst_mod_manager.get_id()
        ):
            raise SameModsLocationDiffManagerError

        elif src_drive != dst_drive or not use_hardlinks:
            available_space: int = get_free_disk_space(dst_drive)
            self.log.debug(
                f"Available space on '{dst_drive}': {scale_value(available_space)}"
            )
            if available_space < src_instance.size:
                raise NotEnoughSpaceError(
                    dst_drive,
                    scale_value(src_instance.size),
                    scale_value(available_space),
                )

        # dst_mod_manager.prepare_migration(dst_info)

        if ldialog is not None:
            ldialog.updateProgress(
                text1=self.tr("Migrating instance {0}...").format(
                    src_info.display_name
                ),
            )

        # Try to load existing instance
        dst_instance: Instance
        try:
            dst_instance = dst_mod_manager.load_instance(
                dst_info,
                modname_limit,
                blacklist,  # , ldialog=ldialog
            )
            self.log.warning("Migrating into existing instance...")
        except InstanceNotFoundError:
            dst_instance = dst_mod_manager.create_instance(
                dst_info,
                src_instance.game_folder,  # , ldialog
            )

        self.log.info(f"Destination order matters: {dst_instance.order_matters}")

        included_mods: list[Mod] = list(
            filter(lambda m: m.installed, src_instance.loadorder)
        )
        self.log.info(f"Included mods: {len(included_mods)}")

        for m, mod in enumerate(included_mods):
            if ldialog is not None:
                ldialog.updateProgress(
                    text1=self.tr("Migrating mods...") + f" ({m}/{len(included_mods)})",
                    value1=m,
                    max1=len(included_mods),
                    show2=True,
                    text2=mod.display_name,
                )

            try:
                if not dst_instance.is_mod_installed(mod) or replace:
                    dst_mod_manager.install_mod(
                        mod,
                        dst_instance,
                        dst_info,
                        src_mod_manager.get_actual_files(mod),
                        use_hardlinks,
                        replace,
                        blacklist,
                        # ldialog,
                    )
                else:
                    self.log.info(
                        f"Skipped already installed mod: {mod.display_name!r}"
                    )
            except Exception as ex:
                self.log.error(
                    f"Failed to migrate mod {mod.display_name!r}: {ex}", exc_info=ex
                )
                report.failed_mods[mod] = ex

        for t, tool in enumerate(included_tools):
            if ldialog is not None:
                ldialog.updateProgress(
                    text1=self.tr("Migrating tools...")
                    + f" ({t}/{len(included_tools)})",
                    value1=t,
                    max1=len(included_tools),
                    show2=True,
                    text2=tool.display_name,
                )

            try:
                dst_mod_manager.add_tool(
                    tool,
                    dst_instance,
                    dst_info,
                    use_hardlinks,
                    replace,
                    blacklist,
                    # ldialog,
                )
            except Exception as ex:
                self.log.error(
                    f"Failed to migrate tool {tool.display_name!r}: {ex}", exc_info=ex
                )
                report.failed_tools[tool] = ex

        try:
            ini_files: list[Path] = src_mod_manager.get_ini_files(
                src_instance, src_info
            )
            dst_mod_manager.import_ini_files(
                ini_files,
                dst_info,
                src_instance.separate_ini_files,
                use_hardlinks,
                replace,
                # ldialog,
            )
        except Exception as ex:
            self.log.error(
                f"Failed to migrate ini files from source to destination: {ex}",
                exc_info=ex,
            )
            report.other_errors[self.tr("Failed to migrate INI files.")] = ex

        try:
            additional_files: list[Path] = src_mod_manager.get_additional_files(
                src_info
            )
            dst_mod_manager.import_additional_files(
                additional_files,
                dst_info,
                use_hardlinks,
                replace,  # , ldialog
            )
        except Exception as ex:
            self.log.error(
                f"Failed to migrate additional files from source to destination: {ex}",
                exc_info=ex,
            )
            report.other_errors[self.tr("Failed to migrate additional files.")] = ex

        dst_mod_manager.finalize_instance(dst_instance, dst_info, activate_new_instance)
        self.log.info("Migration completed.")
        return report

    def get_completed_message(
        self, src_instance_data: InstanceInfo, dst_instance_data: InstanceInfo
    ) -> str:
        """
        Generates a localized message with additional notes for the user to be shown
        after the migration.

        Args:
            src_instance_data (InstanceInfo): Information about the source mod instance.
            dst_instance_data (InstanceInfo):
                Information about the destination mod instance.

        Returns:
            str: Localized message.
        """

        text: str = ""

        if dst_instance_data.get_mod_manager() == ModManager.ModOrganizer:
            migrated_instance_data: MO2InstanceInfo = cast(
                MO2InstanceInfo, dst_instance_data
            )
            mo2: ModOrganizer = cast(ModOrganizer, ModManager.ModOrganizer.get_api())

            if migrated_instance_data.use_root_builder:
                if migrated_instance_data.is_global:
                    text += (
                        self.tr(
                            "The usage of root builder was enabled.\n"
                            "In order to correctly deploy the root files, you have to "
                            "download and extract the root builder plugin from Nexus "
                            'Mods to the "plugins" folder of your MO2 installation if '
                            "not already installed."
                        )
                        + "\n\n"
                    )
                else:
                    text += (
                        self.tr(
                            "The usage of root builder was enabled.\n"
                            "In order to correctly deploy the root files, you have to "
                            "download and extract the root builder plugin from Nexus "
                            'Mods to the "plugins" folder of the new MO2 installation.'
                        )
                        + "\n\n"
                    )

            if not migrated_instance_data.is_global and mo2.detect_global_instances():
                text += (
                    self.tr(
                        "At least one global instance was detected.\n"
                        "Global instances cause issues with portable instances and it is "
                        "recommended to delete (or rename) the following folder:\n{0}"
                    ).format(str(mo2.appdata_path))
                    + "\n\n"
                )

        if (
            dst_instance_data.get_mod_manager() != src_instance_data.get_mod_manager()
            and src_instance_data.get_mod_manager() == ModManager.Vortex
        ):
            vortex: Vortex = cast(Vortex, ModManager.Vortex.get_api())
            if vortex.is_deployed(src_instance_data.game):
                text += self.tr(
                    "Vortex is currently deployed to the game folder. It is strongly "
                    "recommended to purge the game directory before using the migrated "
                    "instance."
                )

        return text
