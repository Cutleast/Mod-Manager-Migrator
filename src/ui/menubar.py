"""
Copyright (c) Cutleast
"""

import webbrowser

import qtawesome as qta
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QMenuBar, QMessageBox

from app_context import AppContext
from core.utilities.path_limit_fixer import PathLimitFixer
from core.utilities.updater import Updater
from ui.settings.settings_dialog import SettingsDialog
from ui.utilities.ui_mode import UIMode
from ui.widgets.about_dialog import AboutDialog
from ui.widgets.menu import Menu


class MenuBar(QMenuBar):
    """
    Menu bar for main window.
    """

    DISCORD_URL: str = "https://discord.gg/pqEHdWDf8z"
    """URL to our Discord server."""

    NEXUSMODS_URL: str = "https://www.nexusmods.com/site/mods/545/"
    """URL to MMM's Nexus Mods page."""

    def __init__(self) -> None:
        super().__init__()

        self.__init_file_menu()
        self.__init_help_menu()

    def __init_file_menu(self) -> None:
        file_menu = Menu(title=self.tr("File"))
        self.addMenu(file_menu)

        settings_action = file_menu.addAction(self.tr("Settings"))
        settings_action.setIcon(
            qta.icon("mdi6.cog", color=self.palette().text().color())
        )
        settings_action.triggered.connect(self.__open_settings)

        file_menu.addSeparator()

        exit_action = file_menu.addAction(self.tr("Exit"))
        exit_action.setIcon(
            QIcon(":/icons/exit_dark.svg")
            if AppContext.get_app().stylesheet_processor.ui_mode == UIMode.Light
            else QIcon(":/icons/exit_light.svg")
        )
        exit_action.triggered.connect(QApplication.exit)

    def __init_help_menu(self) -> None:
        help_menu = Menu(title=self.tr("Help"))
        self.addMenu(help_menu)

        update_action = help_menu.addAction(self.tr("Check for updates..."))
        update_action.setIcon(
            qta.icon("mdi6.refresh", color=self.palette().text().color())
        )
        update_action.triggered.connect(self.__check_for_updates)

        help_menu.addSeparator()

        path_limit_action = help_menu.addAction(self.tr("Fix Windows Path Limit..."))
        path_limit_action.setIcon(
            qta.icon(
                "mdi6.bug-check", color=self.palette().text().color(), scale_factor=1.3
            )
        )
        path_limit_action.triggered.connect(
            lambda: PathLimitFixer.disable_path_limit(AppContext.get_app().res_path)
        )

        help_menu.addSeparator()

        discord_action = help_menu.addAction(
            self.tr("Get support on our Discord server...")
        )
        discord_action.setIcon(QIcon(":/icons/discord.png"))
        discord_action.setToolTip(MenuBar.DISCORD_URL)
        discord_action.triggered.connect(lambda: webbrowser.open(MenuBar.DISCORD_URL))

        nm_action = help_menu.addAction(self.tr("Open mod page on Nexus Mods..."))
        nm_action.setIcon(QIcon(":/icons/nexus_mods.png"))
        nm_action.setToolTip(MenuBar.NEXUSMODS_URL)
        nm_action.triggered.connect(lambda: webbrowser.open(MenuBar.NEXUSMODS_URL))

        help_menu.addSeparator()

        about_action = help_menu.addAction(self.tr("About"))
        about_action.setIcon(
            qta.icon("fa5s.info-circle", color=self.palette().text().color())
        )
        about_action.triggered.connect(self.__show_about)

        about_qt_action = help_menu.addAction(self.tr("About Qt"))
        about_qt_action.triggered.connect(self.__show_about_qt)

    def __open_settings(self) -> None:
        SettingsDialog(AppContext.get_app().app_config).exec()

    def __check_for_updates(self) -> None:
        upd = Updater(AppContext.get_app().APP_VERSION)
        if upd.update_available():
            upd.run()
        else:
            messagebox = QMessageBox(AppContext.get_app().main_window)
            messagebox.setWindowTitle(self.tr("No Updates Available"))
            messagebox.setText(self.tr("There are no updates available."))
            messagebox.setTextFormat(Qt.TextFormat.RichText)
            messagebox.setIcon(QMessageBox.Icon.Information)
            messagebox.exec()

    def __show_about(self) -> None:
        AboutDialog(AppContext.get_app().main_window).exec()

    def __show_about_qt(self) -> None:
        QMessageBox.aboutQt(AppContext.get_app().main_window, self.tr("About Qt"))
