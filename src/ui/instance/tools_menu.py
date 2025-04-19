"""
Copyright (c) Cutleast
"""

from typing import Optional

import qtawesome as qta
from PySide6.QtGui import QAction, QCursor, QIcon

from core.instance.tool import Tool
from ui.widgets.menu import Menu


class ToolsMenu(Menu):
    """
    Contextmenu for ToolsWidget.
    """

    __parent: "ToolsWidget"

    __uncheck_action: QAction
    __check_action: QAction
    __open_modpage_action: QAction
    __open_in_explorer_action: QAction

    def __init__(self, parent: "ToolsWidget") -> None:
        super().__init__()

        self.__parent = parent

        self.__init_item_actions()
        self.__init_open_actions()

    def __init_item_actions(self) -> None:
        expand_all_action: QAction = self.addAction(
            qta.icon("mdi6.arrow-expand-vertical", color=self.palette().text().color()),
            self.tr("Expand all"),
        )
        expand_all_action.triggered.connect(self.__parent.expandAll)

        collapse_all_action: QAction = self.addAction(
            qta.icon(
                "mdi6.arrow-collapse-vertical", color=self.palette().text().color()
            ),
            self.tr("Collapse all"),
        )
        collapse_all_action.triggered.connect(self.__parent.collapseAll)

        self.__uncheck_action = self.addAction(
            qta.icon("fa.close", color=self.palette().text().color()),
            self.tr("Exclude selected tool(s)"),
        )
        self.__uncheck_action.triggered.connect(self.__parent.uncheck_selected)

        self.__check_action = self.addAction(
            qta.icon("fa.check", color=self.palette().text().color()),
            self.tr("Include selected tool(s)"),
        )
        self.__check_action.triggered.connect(self.__parent.check_selected)

        self.addSeparator()

    def __init_open_actions(self) -> None:
        self.__open_modpage_action = self.addAction(
            QIcon(":/icons/nexus_mods.png"),
            self.tr("Open mod page on Nexus Mods..."),
        )
        self.__open_modpage_action.triggered.connect(self.__parent.open_modpage)

        self.__open_in_explorer_action = self.addAction(
            qta.icon("fa5s.folder", color=self.palette().text().color()),
            self.tr("Open in Explorer..."),
        )
        self.__open_in_explorer_action.triggered.connect(self.__parent.open_in_explorer)

    def open(self) -> None:
        """
        Opens the context menu at the current cursor position.
        """

        current_item: Optional[Tool] = self.__parent.get_current_item()

        self.__uncheck_action.setVisible(
            current_item is not None and not current_item.is_in_game_dir
        )
        self.__check_action.setVisible(
            current_item is not None and not current_item.is_in_game_dir
        )
        self.__open_modpage_action.setVisible(
            current_item is not None
            and current_item.mod is not None
            and current_item.mod.get_modpage_url() is not None
        )
        self.__open_in_explorer_action.setVisible(current_item is not None)

        self.exec(QCursor.pos())


if __name__ == "__main__":
    from .tools_widget import ToolsWidget
