"""
Copyright (c) Cutleast
"""

import webbrowser
from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QLabel,
    QLCDNumber,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from core.instance.instance import Instance
from core.instance.tool import Tool
from core.utilities.filesystem import open_in_explorer
from core.utilities.filter import matches_filter
from ui.utilities.tree_widget import iter_toplevel_items
from ui.widgets.search_bar import SearchBar

from .tools_menu import ToolsMenu


class ToolsWidget(QWidget):
    """
    A widget for displaying the loaded instance's tools.
    """

    __instance: Instance

    __vlayout: QVBoxLayout
    __search_bar: SearchBar
    __tools_num_label: QLCDNumber
    __tree_widget: QTreeWidget
    __tools_tree_items: dict[Tool, QTreeWidgetItem]
    __tools_menu: ToolsMenu

    def __init__(self) -> None:
        super().__init__()

        self.__init_ui()

    def __init_ui(self) -> None:
        self.__vlayout = QVBoxLayout()
        self.setLayout(self.__vlayout)

        self.__init_header()
        self.__init_tree_widget()
        self.__init_context_menu()

    def __init_header(self) -> None:
        hlayout = QHBoxLayout()
        self.__vlayout.addLayout(hlayout)

        self.__search_bar = SearchBar()
        self.__search_bar.searchChanged.connect(self.__on_search)
        hlayout.addWidget(self.__search_bar)

        num_label = QLabel(self.tr("Included Tools:"))
        num_label.setObjectName("h3")
        hlayout.addWidget(num_label)

        self.__tools_num_label = QLCDNumber()
        self.__tools_num_label.setDigitCount(4)
        self.__tools_num_label.setSegmentStyle(QLCDNumber.SegmentStyle.Flat)
        hlayout.addWidget(self.__tools_num_label)

    def __init_tree_widget(self) -> None:
        self.__tree_widget = QTreeWidget()
        self.__tree_widget.setUniformRowHeights(True)
        self.__tree_widget.setAlternatingRowColors(True)
        self.__tree_widget.itemChanged.connect(
            lambda _: self.__update_num_label(), Qt.ConnectionType.QueuedConnection
        )
        self.__vlayout.addWidget(self.__tree_widget, stretch=1)

        self.__tree_widget.setHeaderLabels(
            [
                self.tr("Name"),
                self.tr("Mod"),
                self.tr("Executable Path"),
                self.tr("Arguments"),
                self.tr("Working Directory"),
            ]
        )
        self.__tree_widget.header().setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)
        self.__tree_widget.setSelectionMode(
            QAbstractItemView.SelectionMode.ExtendedSelection
        )
        self.__tree_widget.setTextElideMode(Qt.TextElideMode.ElideMiddle)

    def __init_context_menu(self) -> None:
        self.__tools_menu = ToolsMenu(self)
        self.__tree_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.__tree_widget.customContextMenuRequested.connect(self.__tools_menu.open)

    def __update_num_label(self) -> None:
        self.__tools_num_label.display(
            len(
                [
                    i
                    for i in self.__tools_tree_items.values()
                    if i.checkState(0) == Qt.CheckState.Checked and not i.isHidden()
                ]
            )
        )

    def __on_search(self, text: str, case_sensitive: bool) -> None:
        for item in iter_toplevel_items(self.__tree_widget):
            item.setHidden(
                all(
                    not matches_filter(item.text(i), text, case_sensitive)
                    for i in range(5)
                )
            )

        self.__update_num_label()

    def display_modinstance(self, instance: Instance) -> None:
        """
        Displays the tools of the specified mod instance.

        Args:
            instance (Instance): The instance to display
        """

        self.__instance = instance
        self.__tools_num_label.display(len(instance.tools))

        self.__tree_widget.clear()
        self.__tools_tree_items = {}
        for tool in instance.tools:
            item = ToolsWidget._create_tool_item(
                tool, instance.game_folder, instance.last_tool == tool
            )
            self.__tools_tree_items[tool] = item
            self.__tree_widget.addTopLevelItem(item)

        self.__tree_widget.resizeColumnToContents(0)
        self.__tree_widget.resizeColumnToContents(1)

    @staticmethod
    def _create_tool_item(
        tool: Tool, game_folder: Path, last_active: bool
    ) -> QTreeWidgetItem:
        item = QTreeWidgetItem(
            [
                tool.display_name,
                str(tool.mod.display_name if tool.mod is not None else ""),
                str(tool.executable),
                " ".join(tool.commandline_args),
                str(tool.working_dir or ""),
            ]
        )
        item.setToolTip(2, str(tool.get_full_executable_path(game_folder)))
        item.setToolTip(3, " ".join(tool.commandline_args))
        if tool.working_dir is not None:
            item.setToolTip(4, str(tool.working_dir))
        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)

        if tool.get_full_executable_path(game_folder).is_file():
            item.setCheckState(0, Qt.CheckState.Checked)
        else:
            item.setCheckState(0, Qt.CheckState.Unchecked)
            item.setDisabled(True)

        font = QFont()
        font.setBold(last_active)
        font.setItalic(tool.is_in_game_dir)
        item.setFont(0, font)

        return item

    @property
    def checked_tools(self) -> list[Tool]:
        """
        A list of currently checked tools.
        """

        return [
            tool
            for tool, item in self.__tools_tree_items.items()
            if item.checkState(0) == Qt.CheckState.Checked
        ]

    def expandAll(self) -> None:
        self.__tree_widget.expandAll()

    def collapseAll(self) -> None:
        self.__tree_widget.collapseAll()

    def check_selected(self) -> None:
        for item in self.__tree_widget.selectedItems():
            if (
                Qt.ItemFlag.ItemIsUserCheckable in item.flags()
                and Qt.ItemFlag.ItemIsEditable in item.flags()
            ):
                item.setCheckState(0, Qt.CheckState.Checked)

    def uncheck_selected(self) -> None:
        for item in self.__tree_widget.selectedItems():
            if (
                Qt.ItemFlag.ItemIsUserCheckable in item.flags()
                and Qt.ItemFlag.ItemIsEditable in item.flags()
            ):
                item.setCheckState(0, Qt.CheckState.Unchecked)

    def open_modpage(self) -> None:
        current_item: Optional[Tool] = self.get_current_item()

        if isinstance(current_item, Tool) and current_item.mod is not None:
            url: Optional[str] = current_item.mod.get_modpage_url()

            if url is not None:
                webbrowser.open(url)

    def open_in_explorer(self) -> None:
        current_item: Optional[Tool] = self.get_current_item()

        if current_item is not None:
            open_in_explorer(
                current_item.get_full_executable_path(self.__instance.game_folder)
            )

    def get_current_item(self) -> Optional[Tool]:
        items: dict[QTreeWidgetItem, Tool] = {
            item: mod for mod, item in self.__tools_tree_items.items()
        }
        current_item: Optional[Tool] = items.get(self.__tree_widget.currentItem())

        return current_item
