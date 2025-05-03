"""
Copyright (c) Cutleast
"""

import logging
from pathlib import Path
from typing import Optional

from PySide6.QtCore import QObject

from core.instance.instance import Instance
from core.instance.tool import Tool
from core.mod_manager.exceptions import InstanceNotFoundError
from core.mod_manager.instance_info import InstanceInfo
from core.mod_manager.mod_manager import ModManager
from core.utilities.exceptions import NotEnoughSpaceError
from core.utilities.filesystem import get_free_disk_space
from core.utilities.logger import Logger
from core.utilities.scale import scale_value
from ui.widgets.loading_dialog import LoadingDialog

from .file_blacklist import FileBlacklist
from .migration_report import MigrationReport


class Migrator(QObject):
    """
    Class that handles the migration process.
    """

    log: logging.Logger = logging.getLogger("Migrator")

    def migrate(
        self,
        src_instance: Instance,
        src_info: InstanceInfo,
        dst_info: InstanceInfo,
        src_mod_manager: ModManager,
        dst_mod_manager: ModManager,
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
            src_info (InstanceInfo): Information about the source mod instance.
            dst_info (InstanceInfo): Information about the destination mod instance.
            src_mod_manager (ModManager): Source mod manager.
            dst_mod_manager (ModManager): Destination mod manager.
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

        Returns:
            MigrationReport: A report containing migration errors.
        """

        self.log.info(
            f"Migrating instance {src_info.display_name!r} from "
            f"{src_mod_manager.get_display_name()} to "
            f"{dst_mod_manager.get_display_name()}..."
        )

        report = MigrationReport()

        self.log.info("Source instance info:")
        Logger.log_str_dict(self.log, src_info.__dict__)
        self.log.info(f"Source size: {scale_value(src_instance.size)}")

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

        src_drive: str = src_mod_manager.get_mods_path(src_info).drive
        dst_drive: str = dst_mod_manager.get_mods_path(dst_info).drive

        if src_drive != dst_drive or not use_hardlinks:
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

        dst_mod_manager.prepare_migration(dst_info)

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
                dst_info, modname_limit, blacklist, ldialog=ldialog
            )
            self.log.warning("Migrating into existing instance...")
        except InstanceNotFoundError:
            dst_instance = dst_mod_manager.create_instance(
                dst_info, src_instance.game_folder, ldialog
            )

        for m, mod in enumerate(src_instance.mods):
            if ldialog is not None:
                ldialog.updateProgress(
                    text1=self.tr("Migrating mods...")
                    + f" ({m}/{len(src_instance.mods)})",
                    value1=m,
                    max1=len(src_instance.mods),
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
                        ldialog,
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
                    ldialog,
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
            dst_mod_manager.migrate_ini_files(
                ini_files,
                dst_info,
                src_instance.separate_ini_files,
                use_hardlinks,
                replace,
                ldialog,
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
            dst_mod_manager.migrate_additional_files(
                additional_files, dst_info, use_hardlinks, replace, ldialog
            )
        except Exception as ex:
            self.log.error(
                f"Failed to migrate additional files from source to destination: {ex}",
                exc_info=ex,
            )
            report.other_errors[self.tr("Failed to migrate additional files.")] = ex

        dst_mod_manager.finalize_migration(
            dst_instance, dst_info, src_instance.order_matters, activate_new_instance
        )
        self.log.info("Migration completed.")
        return report
