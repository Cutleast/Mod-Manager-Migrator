"""
Copyright (c) Cutleast
"""

import os
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLCDNumber,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from core.instance.instance import Instance
from core.instance.mod import Mod
from core.utilities.filter import matches_filter
from core.utilities.scale import scale_value
from ui.instance.modlist_menu import ModlistMenu
from ui.utilities.tree_widget import iter_children, iter_toplevel_items
from ui.widgets.search_bar import SearchBar


class ModlistWidget(QWidget):
    """
    Combo-widget for displaying a modlist and some info about it.
    """

    __vlayout: QVBoxLayout
    __instance_name_label: QLabel
    __mods_num_label: QLCDNumber
    __search_bar: SearchBar
    __tree_widget: QTreeWidget
    __modlist_tree_items: dict[Mod, QTreeWidgetItem]
    __modlist_menu: ModlistMenu

    def __init__(self) -> None:
        super().__init__()

        self.__init_ui()

    def __init_ui(self) -> None:
        self.__vlayout = QVBoxLayout()
        self.setLayout(self.__vlayout)

        self.__init_header()
        self.__init_search_bar()
        self.__init_tree_widget()
        self.__init_context_menu()

    def __init_header(self) -> None:
        hlayout = QHBoxLayout()
        self.__vlayout.addLayout(hlayout)

        self.__instance_name_label = QLabel()
        self.__instance_name_label.setObjectName("h2")
        hlayout.addWidget(self.__instance_name_label)

        hlayout.addStretch()

        num_label = QLabel(self.tr("Active Mods:"))
        num_label.setObjectName("h3")
        hlayout.addWidget(num_label)

        self.__mods_num_label = QLCDNumber()
        self.__mods_num_label.setDigitCount(4)
        self.__mods_num_label.setSegmentStyle(QLCDNumber.SegmentStyle.Flat)
        hlayout.addWidget(self.__mods_num_label)

    def __init_search_bar(self) -> None:
        self.__search_bar = SearchBar()
        self.__search_bar.searchChanged.connect(self.__on_search)
        self.__vlayout.addWidget(self.__search_bar)

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
                self.tr("Version"),
                self.tr("Size"),
                self.tr("Priority"),
            ]
        )
        self.__tree_widget.header().setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)
        self.__tree_widget.setSelectionMode(
            QAbstractItemView.SelectionMode.ExtendedSelection
        )
        self.__tree_widget.header().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )
        self.__tree_widget.header().setStretchLastSection(False)

    def __init_context_menu(self) -> None:
        self.__modlist_menu = ModlistMenu(self)
        self.__tree_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.__tree_widget.customContextMenuRequested.connect(self.__modlist_menu.open)

    def __on_search(self, text: str, case_sensitive: bool) -> None:
        for item in iter_toplevel_items(self.__tree_widget):
            for child in iter_children(item):
                child.setHidden(not matches_filter(child.text(0), text, case_sensitive))

            item.setHidden(
                not matches_filter(item.text(0), text, case_sensitive)
                and all(child.isHidden() for child in iter_children(item))
            )

        self.__update_num_label()

    @property
    def checked_mods(self) -> list[Mod]:
        """
        A list of currently checked mods.
        """

        return [
            mod
            for mod, item in self.__modlist_tree_items.items()
            if item.checkState(0) == Qt.CheckState.Checked
        ]

    def __update_num_label(self) -> None:
        self.__mods_num_label.display(
            len(
                [
                    i
                    for i in self.__modlist_tree_items.values()
                    if i.checkState(0) == Qt.CheckState.Checked and not i.isHidden()
                ]
            )
        )

    def display_modinstance(self, instance: Instance) -> None:
        """
        Displays a modlist.

        Args:
            instance (Instance): The instance to display.
        """

        self.__instance_name_label.setText(instance.display_name)
        self.__mods_num_label.display(len([m for m in instance.mods if m.enabled]))

        self.__tree_widget.clear()
        self.__modlist_tree_items = {}

        cur_separator: Optional[QTreeWidgetItem] = None
        for i, mod in enumerate(instance.loadorder):
            # Process separator
            if mod.mod_type == Mod.Type.Separator:
                cur_separator = ModlistWidget._create_separator_item(mod, i)
                self.__modlist_tree_items[mod] = cur_separator
                self.__tree_widget.addTopLevelItem(cur_separator)

            # Process mod
            else:
                mod_item = ModlistWidget._create_mod_item(mod, i)
                self.__modlist_tree_items[mod] = mod_item

                if cur_separator is not None:
                    cur_separator.addChild(mod_item)
                else:
                    self.__tree_widget.addTopLevelItem(mod_item)

    @staticmethod
    def _create_separator_item(separator: Mod, index: int) -> QTreeWidgetItem:
        separator_item = QTreeWidgetItem(
            [
                separator.display_name,
                "",  # Version
                "",  # Size
                str(index + 1),  # Mod Priority
            ]
        )
        separator_item.setTextAlignment(0, Qt.AlignmentFlag.AlignCenter)
        separator_item.setTextAlignment(3, Qt.AlignmentFlag.AlignCenter)
        font = QFont()
        font.setBold(True)
        font.setItalic(True)
        separator_item.setFont(0, font)
        separator_item.setFlags(Qt.ItemFlag.ItemIsSelectable)
        separator_item.setToolTip(0, separator_item.text(0))
        separator_item.setDisabled(False)

        return separator_item

    @staticmethod
    def _create_mod_item(mod: Mod, index: int) -> QTreeWidgetItem:
        mod_item = QTreeWidgetItem(
            [
                mod.display_name,
                mod.metadata.version,
                scale_value(mod.size),
                str(index + 1),  # Mod Priority
            ]
        )
        mod_item.setToolTip(0, mod_item.text(0))
        mod_item.setDisabled(False)
        mod_item.setTextAlignment(1, Qt.AlignmentFlag.AlignCenter)
        mod_item.setTextAlignment(2, Qt.AlignmentFlag.AlignCenter)
        mod_item.setTextAlignment(3, Qt.AlignmentFlag.AlignCenter)
        mod_item.setFlags(mod_item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
        mod_item.setCheckState(
            0, Qt.CheckState.Checked if mod.enabled else Qt.CheckState.Unchecked
        )

        return mod_item

    def expandAll(self) -> None:
        self.__tree_widget.expandAll()

    def collapseAll(self) -> None:
        self.__tree_widget.collapseAll()

    def check_selected(self) -> None:
        for item in self.__tree_widget.selectedItems():
            if Qt.ItemFlag.ItemIsUserCheckable in item.flags():
                item.setCheckState(0, Qt.CheckState.Checked)

    def uncheck_selected(self) -> None:
        for item in self.__tree_widget.selectedItems():
            if Qt.ItemFlag.ItemIsUserCheckable in item.flags():
                item.setCheckState(0, Qt.CheckState.Unchecked)

    def open_modpage(self) -> None:
        current_item: Optional[Mod] = self.get_current_item()

        if isinstance(current_item, Mod):
            url: Optional[str] = current_item.get_modpage_url()

            if url is not None:
                os.startfile(url)

    def open_in_explorer(self) -> None:
        current_item: Optional[Mod] = self.get_current_item()

        if current_item is not None:
            os.startfile(current_item.path)

    def get_current_item(self) -> Optional[Mod]:
        items: dict[QTreeWidgetItem, Mod] = {
            item: mod for mod, item in self.__modlist_tree_items.items()
        }
        current_item: Optional[Mod] = items.get(self.__tree_widget.currentItem())

        return current_item
