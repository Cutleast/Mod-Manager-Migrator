"""
Copyright (c) Cutleast
"""

from PySide6.QtWidgets import QTabWidget

from core.instance.instance import Instance
from core.instance.mod import Mod
from core.instance.tool import Tool

from .modlist_widget import ModlistWidget
from .tools_widget import ToolsWidget


class InstanceWidget(QTabWidget):
    """
    A tab widget displaying two tabs: modlist and tools.
    """

    __modlist_tab: ModlistWidget
    __tools_tab: ToolsWidget

    def __init__(self) -> None:
        super().__init__()

        self.tabBar().setDocumentMode(True)

        self.__modlist_tab = ModlistWidget()
        self.__tools_tab = ToolsWidget()

        self.addTab(self.__modlist_tab, self.tr("Modlist"))
        self.addTab(self.__tools_tab, self.tr("Tools"))

    def display_modinstance(self, instance: Instance) -> None:
        """
        Displays a mod instance.

        Args:
            instance (Instance): The instance to display.
        """

        self.__modlist_tab.display_modinstance(instance)
        self.__tools_tab.display_modinstance(instance)

    @property
    def checked_mods(self) -> list[Mod]:
        """
        A list of currently checked mods.
        """

        return self.__modlist_tab.checked_mods

    @property
    def checked_tools(self) -> list[Tool]:
        """
        A list of currently checked tools.
        """

        return self.__tools_tab.checked_tools
