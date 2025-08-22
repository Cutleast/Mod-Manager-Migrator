"""
Copyright (c) Cutleast
"""

import logging
from typing import override

from cutleast_core_lib.core.utilities.path_limit_fixer import PathLimitFixer
from cutleast_core_lib.core.utilities.updater import Updater
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMainWindow, QMessageBox

from core.config.app_config import AppConfig
from core.utilities.licenses import LICENSES

from .main_widget import MainWidget
from .menubar import MenuBar
from .settings.settings_dialog import SettingsDialog
from .statusbar import StatusBar
from .widgets.about_dialog import AboutDialog


class MainWindow(QMainWindow):
    """
    Main window of the application.
    """

    __app_config: AppConfig

    __menu_bar: MenuBar
    __main_widget: MainWidget
    __status_bar: StatusBar

    log: logging.Logger = logging.getLogger("App")

    def __init__(self, app_config: AppConfig) -> None:
        super().__init__()

        self.__app_config = app_config

        self.resize(1300, 800)

        self.__init_ui()

        self.__menu_bar.settings_signal.connect(self.__open_settings)
        self.__menu_bar.updater_signal.connect(self.__check_for_updates)
        self.__menu_bar.fix_path_limit_signal.connect(self.__fix_path_limit)
        self.__menu_bar.about_signal.connect(self.__show_about)
        self.__menu_bar.about_qt_signal.connect(self.__show_about_qt)
        self.__menu_bar.exit_signal.connect(self.close)

    def __init_ui(self) -> None:
        self.__init_menu_bar()
        self.__init_main_widget()
        self.__init_status_bar()

    def __init_menu_bar(self) -> None:
        self.__menu_bar = MenuBar()
        self.setMenuBar(self.__menu_bar)

    def __init_main_widget(self) -> None:
        self.__main_widget = MainWidget(self.__app_config)
        self.setCentralWidget(self.__main_widget)

    def __init_status_bar(self) -> None:
        self.__status_bar = StatusBar(self.__app_config.log_visible)
        self.setStatusBar(self.__status_bar)

    @override
    def show(self) -> None:
        super().show()

        self.__detect_path_limit()
        self.__menu_bar.setUpdateActionVisible(Updater.has_instance())

    def __open_settings(self) -> None:
        SettingsDialog(self.__app_config).exec()

    def __check_for_updates(self) -> None:
        upd = Updater.get()
        if upd.is_update_available():
            upd.run()
        else:
            messagebox = QMessageBox(self)
            messagebox.setWindowTitle(self.tr("No Updates Available"))
            messagebox.setText(self.tr("There are no updates available."))
            messagebox.setTextFormat(Qt.TextFormat.RichText)
            messagebox.setIcon(QMessageBox.Icon.Information)
            messagebox.exec()

    def __show_about(self) -> None:
        from app import App

        AboutDialog(
            app_name=App.APP_NAME,
            app_version=App.APP_VERSION,
            app_icon=App.get().windowIcon(),
            app_license="",
            licenses=LICENSES,
            parent=self,
        ).exec()

    def __show_about_qt(self) -> None:
        QMessageBox.aboutQt(self, self.tr("About Qt"))

    def __detect_path_limit(self) -> None:
        """
        Detects if the NTFS path length limit is enabled and asks if the user wants to
        disable it.
        """

        path_limit_enabled: bool = PathLimitFixer.is_path_limit_enabled()
        self.log.info(f"Path length limit enabled: {path_limit_enabled}")

        if path_limit_enabled:
            reply = QMessageBox.question(
                self,
                self.tr("Path Limit Enabled"),
                self.tr(
                    "The NTFS path length limit is enabled and paths longer than 255 "
                    "characters will cause issues. Would you like to disable it "
                    "(admin rights may be required)? "
                    "A reboot is required for this to take effect."
                ),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )

            if reply == QMessageBox.StandardButton.Yes:
                self.__fix_path_limit()

    def __fix_path_limit(self) -> None:
        from app import App

        PathLimitFixer.disable_path_limit(App.get().res_path)
