"""
Copyright (c) Cutleast
"""

from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMessageBox, QSplitter

from app_context import AppContext
from core.config.app_config import AppConfig
from core.game.game import Game
from core.instance.instance import Instance
from core.instance.mod import Mod
from core.migrator.migration_report import MigrationReport
from core.migrator.migrator import Migrator
from core.mod_manager.instance_info import InstanceInfo
from core.mod_manager.mod_manager import ModManager
from ui.instance.instance_widget import InstanceWidget
from ui.migrator.migration_report_dialog import MigrationReportDialog
from ui.migrator.migrator_widget import MigratorWidget
from ui.widgets.loading_dialog import LoadingDialog


class MainWidget(QSplitter):
    """
    Class for main widget containing the migrator widget and the loaded instance widget.
    """

    __migrator_widget: MigratorWidget
    __instance_widget: InstanceWidget

    def __init__(self) -> None:
        super().__init__()

        self.__init_ui()

        self.__migrator_widget.src_selected.connect(self.__display_modinstance)
        AppContext.get_app().migration_signal.connect(self.migrate)

    def __init_ui(self) -> None:
        self.setOrientation(Qt.Orientation.Horizontal)

        self.__init_migrator_widget()
        self.__init_modlist()

        self.setSizes([self.width(), 0])

    def __init_migrator_widget(self) -> None:
        self.__migrator_widget = MigratorWidget()
        self.addWidget(self.__migrator_widget)

        self.__migrator_widget.setMinimumWidth(500)

    def __init_modlist(self) -> None:
        self.__instance_widget = InstanceWidget()
        self.setCollapsible(1, True)
        self.addWidget(self.__instance_widget)

    def __display_modinstance(self, instance: Instance) -> None:
        self.__instance_widget.display_modinstance(instance)
        self.setSizes([int(0.3 * self.width()), int(0.7 * self.width())])

    def migrate(self) -> None:
        """
        Initiates migration of the selected source instance to the customized
        destination instance.
        """

        game: Optional[Game] = self.__migrator_widget.get_selected_game()
        if game is None:
            raise ValueError("No game selected!")

        src_mod_manager: Optional[ModManager] = (
            self.__migrator_widget.get_src_mod_manager()
        )

        dst_mod_manager: Optional[ModManager] = (
            self.__migrator_widget.get_dst_mod_manager()
        )

        if src_mod_manager is None or dst_mod_manager is None:
            raise ValueError("No mod manager selected!")

        dst_info: Optional[InstanceInfo] = self.__migrator_widget.get_dst_instance_info(
            game
        )

        if dst_info is None:
            raise ValueError("No destination instance selected!")

        src_instance: Optional[Instance] = self.__migrator_widget.get_src_instance()
        src_info: Optional[InstanceInfo] = (
            self.__migrator_widget.get_src_instance_info()
        )

        if src_info is None or src_instance is None:
            raise ValueError("No source instance selected!")

        MainWidget._apply_checked_mods(
            src_instance, self.__instance_widget.checked_mods
        )

        app_config: AppConfig = AppContext.get_app().app_config

        report: MigrationReport = LoadingDialog.run_callable(
            lambda ldialog: Migrator().migrate(
                src_instance=src_instance,
                src_info=src_info,
                dst_info=dst_info,
                src_mod_manager=src_mod_manager,
                dst_mod_manager=dst_mod_manager,
                use_hardlinks=app_config.use_hardlinks,
                replace=app_config.replace_when_merge,
                modname_limit=app_config.modname_limit,
                activate_new_instance=app_config.activate_new_instance,
                included_tools=self.__instance_widget.checked_tools,
                ldialog=ldialog,
            ),
            parent=AppContext.get_app().main_window,
        )

        if report.has_errors:
            QMessageBox.warning(
                AppContext.get_app().main_window,
                self.tr("Migration completed with errors!"),
                (
                    self.tr(
                        "Migration completed with errors! Click 'Ok' to open the report.\n\n"
                    )
                    + dst_mod_manager.get_completed_message(dst_info)
                ).strip(),
                QMessageBox.StandardButton.Ok,
            )

            MigrationReportDialog(report).exec()
        else:
            QMessageBox.information(
                AppContext.get_app().main_window,
                self.tr("Migration Complete"),
                (
                    self.tr("Migration completed successfully!\n\n")
                    + dst_mod_manager.get_completed_message(dst_info)
                ).strip(),
                QMessageBox.StandardButton.Ok,
            )

    @staticmethod
    def _apply_checked_mods(instance: Instance, checked_mods: list[Mod]) -> None:
        for mod in instance.mods:
            mod.enabled = mod in checked_mods
