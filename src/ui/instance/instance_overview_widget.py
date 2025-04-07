"""
Copyright (c) Cutleast
"""

from typing import Optional

import qtawesome as qta
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QMessageBox, QSplitter, QVBoxLayout, QWidget

from app_context import AppContext
from core.config.app_config import AppConfig
from core.game.game import Game
from core.instance.instance import Instance
from core.instance.mod import Mod
from core.migrator.migration_report import MigrationReport
from core.migrator.migrator import Migrator
from core.mod_manager.instance_info import InstanceInfo
from core.mod_manager.mod_manager import ModManager
from ui.migrator.migration_report_dialog import MigrationReportDialog
from ui.widgets.loading_dialog import LoadingDialog
from ui.widgets.smooth_scroll_area import SmoothScrollArea

from ..instance_creator.instance_creator import InstanceCreator
from ..instance_selector.instance_selector import InstanceSelector
from .modlist_widget import ModlistWidget


class InstanceOverviewWidget(QSplitter):
    """
    Class for displaying the migrated modlist.
    """

    __sidebar_widget: SmoothScrollArea
    __instance_selector: InstanceSelector
    __instance_creator: InstanceCreator
    __modlist_widget: ModlistWidget

    def __init__(self) -> None:
        super().__init__()

        self.__init_ui()

        AppContext.get_app().migration_signal.connect(self.migrate)

    def __init_ui(self) -> None:
        self.setOrientation(Qt.Orientation.Horizontal)

        self.__init_sidebar()
        self.__init_modlist()

        self.setSizes([self.width(), 0])

    def __init_sidebar(self) -> None:
        self.__sidebar_widget = SmoothScrollArea()
        self.addWidget(self.__sidebar_widget)

        scroll_widget = QWidget()
        scroll_widget.setObjectName("transparent")
        self.__sidebar_widget.setWidget(scroll_widget)

        vlayout = QVBoxLayout()
        scroll_widget.setLayout(vlayout)

        self.__instance_selector = InstanceSelector()
        self.__instance_selector.instance_selected.connect(self.display_modinstance)
        self.__instance_selector.instance_selected.connect(
            lambda _: self.setSizes([int(0.3 * self.width()), int(0.7 * self.width())])
        )
        vlayout.addWidget(self.__instance_selector, stretch=1)

        vlayout.addStretch()

        right_arrow = QLabel()
        right_arrow.setAlignment(Qt.AlignmentFlag.AlignCenter)
        right_arrow.setPixmap(
            qta.icon("mdi6.chevron-down", color="#ffffff", scale_factor=2).pixmap(
                96, 96
            )
        )
        vlayout.addWidget(right_arrow)

        vlayout.addStretch()

        self.__instance_creator = InstanceCreator()
        self.__instance_creator.setDisabled(True)
        vlayout.addWidget(self.__instance_creator, stretch=1)

        self.__sidebar_widget.setMinimumWidth(500)

    def __init_modlist(self) -> None:
        self.__modlist_widget = ModlistWidget()
        self.setCollapsible(1, True)
        self.addWidget(self.__modlist_widget)

    def display_modinstance(self, instance: Instance) -> None:
        """
        Displays a modlist.

        Args:
            instance (Instance): The instance to display.
        """

        self.__modlist_widget.display_modinstance(instance)
        self.__instance_creator.setEnabled(True)

    def migrate(self) -> None:
        """
        Initiates migration of the selected source instance to the customized
        destination instance.
        """

        game: Optional[Game] = self.__instance_selector.get_cur_game()
        if game is None:
            raise ValueError("No game selected!")

        src_mod_manager: Optional[ModManager] = (
            self.__instance_selector.get_selected_mod_manager()
        )

        dst_mod_manager: Optional[ModManager] = (
            self.__instance_creator.get_selected_mod_manager()
        )

        if src_mod_manager is None or dst_mod_manager is None:
            raise ValueError("No mod manager selected!")

        dst_info: InstanceInfo = self.__instance_creator.get_instance_data(game)
        src_instance: Optional[Instance] = (
            self.__instance_selector.get_cur_mod_instance()
        )
        src_info: InstanceInfo = self.__instance_selector.get_cur_instance_data()

        if src_instance is None:
            raise ValueError("No source instance selected!")

        InstanceOverviewWidget._apply_checked_mods(
            src_instance, self.__modlist_widget.checked_mods
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
