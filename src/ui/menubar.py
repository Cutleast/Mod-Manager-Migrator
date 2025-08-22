"""
Copyright (c) Cutleast
"""

import webbrowser

from cutleast_core_lib.ui.utilities.icon_provider import IconProvider
from cutleast_core_lib.ui.widgets.menu import Menu
from PySide6.QtCore import Signal
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import QMenuBar


class MenuBar(QMenuBar):
    """
    Menu bar for main window.
    """

    settings_signal = Signal()
    """Signal emitted when the user clicks on the settings button."""

    updater_signal = Signal()
    """Signal emitted when the user clicks on the updater button."""

    fix_path_limit_signal = Signal()
    """Signal emitted when the user clicks on the fix path limit button."""

    about_signal = Signal()
    """Signal emitted when the user clicks on the about button."""

    about_qt_signal = Signal()
    """Signal emitted when the user clicks on the about Qt button."""

    exit_signal = Signal()
    """Signal emitted when the user clicks on the exit button."""

    DISCORD_URL: str = "https://discord.gg/pqEHdWDf8z"
    """URL to our Discord server."""

    NEXUSMODS_URL: str = "https://www.nexusmods.com/site/mods/545/"
    """URL to MMM's Nexus Mods page."""

    GITHUB_URL: str = "https://github.com/Cutleast/Mod-Manager-Migrator"
    """URL to the GitHub repository."""

    __update_action: QAction

    def __init__(self) -> None:
        super().__init__()

        self.__init_file_menu()
        self.__init_help_menu()

    def __init_file_menu(self) -> None:
        file_menu = Menu(title=self.tr("File"))
        self.addMenu(file_menu)

        settings_action = file_menu.addAction(self.tr("Settings"))
        settings_action.setIcon(IconProvider.get_qta_icon("mdi6.cog"))
        settings_action.triggered.connect(self.settings_signal.emit)

        file_menu.addSeparator()

        exit_action = file_menu.addAction(self.tr("Exit"))
        exit_action.setIcon(IconProvider.get_icon("exit"))
        exit_action.triggered.connect(self.exit_signal.emit)

    def __init_help_menu(self) -> None:
        help_menu = Menu(title=self.tr("Help"))
        self.addMenu(help_menu)

        self.__update_action = help_menu.addAction(self.tr("Check for updates..."))
        self.__update_action.setIcon(IconProvider.get_qta_icon("mdi6.refresh"))
        self.__update_action.triggered.connect(self.updater_signal.emit)

        help_menu.addSeparator()

        path_limit_action = help_menu.addAction(self.tr("Fix Windows Path Limit..."))
        path_limit_action.setIcon(IconProvider.get_qta_icon("mdi6.bug-check"))
        path_limit_action.triggered.connect(self.fix_path_limit_signal.emit)

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

        github_action = help_menu.addAction(self.tr("View source code on GitHub..."))
        github_action.setIcon(IconProvider.get_qta_icon("mdi6.github"))
        github_action.setToolTip(MenuBar.GITHUB_URL)
        github_action.triggered.connect(lambda: webbrowser.open(MenuBar.GITHUB_URL))

        help_menu.addSeparator()

        about_action = help_menu.addAction(self.tr("About"))
        about_action.setIcon(IconProvider.get_qta_icon("fa5s.info-circle"))
        about_action.triggered.connect(self.about_signal.emit)

        about_qt_action = help_menu.addAction(self.tr("About Qt"))
        about_qt_action.triggered.connect(self.about_qt_signal.emit)

    def setUpdateActionVisible(self, visible: bool) -> None:
        """
        Sets the visibility of the update action.

        Args:
            visible (bool): Whether the action should be visible.
        """

        self.__update_action.setVisible(visible)
