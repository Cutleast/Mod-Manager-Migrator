"""
Copyright (c) Cutleast
"""

import pytest
from cutleast_core_lib.test.utils import Utils
from cutleast_core_lib.ui.widgets.search_bar import SearchBar
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QLCDNumber, QTreeWidget, QTreeWidgetItem
from pytestqt.qtbot import QtBot

from core.instance.instance import Instance
from core.instance.mod import Mod
from tests.base_test import BaseTest
from ui.instance.modlist_widget import ModlistWidget


class TestModlistWidget(BaseTest):
    """
    Tests `ui.instance.modlist_widget.ModlistWidget`.
    """

    INSTANCE_NAME_LABEL: tuple[str, type[QLabel]] = ("instance_name_label", QLabel)
    """Identifier for accessing the private instance_name_label field."""

    MODS_NUM_LABEL: tuple[str, type[QLCDNumber]] = ("mods_num_label", QLCDNumber)
    """Identifier for accessing the private mods_num_label field."""

    SEARCH_BAR: tuple[str, type[SearchBar]] = ("search_bar", SearchBar)
    """Identifier for accessing the private search_bar field."""

    TREE_WIDGET: tuple[str, type[QTreeWidget]] = ("tree_widget", QTreeWidget)
    """Identifier for accessing the private tree_widget field."""

    MODLIST_TREE_ITEMS: tuple[str, type[dict[Mod, QTreeWidgetItem]]] = (
        "modlist_tree_items",
        dict[Mod, QTreeWidgetItem],
    )
    """Identifier for accessing the private modlist_tree_items field."""

    @pytest.fixture
    def widget(self, qtbot: QtBot) -> ModlistWidget:
        """
        Creates an instance of the ModlistWidget to test.

        Returns:
            ModlistWidget: A new ModlistWidget instance.
        """

        widget = ModlistWidget()
        qtbot.addWidget(widget)
        return widget

    def test_initial_state(self, widget: ModlistWidget) -> None:
        """
        Tests the initial state of the ModlistWidget.
        """

        # given
        instance_name_label: QLabel = Utils.get_private_field(
            widget, *TestModlistWidget.INSTANCE_NAME_LABEL
        )
        mods_num_label: QLCDNumber = Utils.get_private_field(
            widget, *TestModlistWidget.MODS_NUM_LABEL
        )
        search_bar: SearchBar = Utils.get_private_field(
            widget, *TestModlistWidget.SEARCH_BAR
        )
        tree_widget: QTreeWidget = Utils.get_private_field(
            widget, *TestModlistWidget.TREE_WIDGET
        )
        modlist_tree_items: dict[Mod, QTreeWidgetItem] = Utils.get_private_field(
            widget, *TestModlistWidget.MODLIST_TREE_ITEMS
        )

        # then
        assert instance_name_label.text() == ""
        assert mods_num_label.value() == 0
        assert search_bar.text() == ""
        assert tree_widget.topLevelItemCount() == 0
        assert modlist_tree_items == {}

    def test_display_modinstance(
        self, instance: Instance, widget: ModlistWidget
    ) -> None:
        """
        Tests displaying a mod instance in the ModlistWidget.
        """

        # given
        instance_name_label: QLabel = Utils.get_private_field(
            widget, *TestModlistWidget.INSTANCE_NAME_LABEL
        )
        mods_num_label: QLCDNumber = Utils.get_private_field(
            widget, *TestModlistWidget.MODS_NUM_LABEL
        )
        tree_widget: QTreeWidget = Utils.get_private_field(
            widget, *TestModlistWidget.TREE_WIDGET
        )
        modlist_tree_items: dict[Mod, QTreeWidgetItem] = Utils.get_private_field(
            widget, *TestModlistWidget.MODLIST_TREE_ITEMS
        )

        # when
        widget.display_modinstance(instance)

        # then
        assert instance_name_label.text() == instance.display_name
        assert mods_num_label.value() == len(instance.mods)
        assert tree_widget.topLevelItemCount() == (
            len(list(filter(lambda m: m.mod_type == Mod.Type.Separator, instance.mods)))
            + 1  # Overwrite mod
        )
        assert len(modlist_tree_items) == len(instance.mods)

    def test_item_changed(
        self, instance: Instance, widget: ModlistWidget, qtbot: QtBot
    ) -> None:
        """
        Tests that items are correctly updated when their checkstate changes.
        """

        # given
        tree_widget: QTreeWidget = Utils.get_private_field(
            widget, *TestModlistWidget.TREE_WIDGET
        )
        modlist_tree_items: dict[Mod, QTreeWidgetItem] = Utils.get_private_field(
            widget, *TestModlistWidget.MODLIST_TREE_ITEMS
        )

        # when
        widget.display_modinstance(instance)
        test_item: QTreeWidgetItem = list(modlist_tree_items.values())[0]

        with qtbot.waitSignal(tree_widget.itemChanged):
            test_item.setCheckState(0, Qt.CheckState.Unchecked)

        # then
        assert test_item.checkState(0) == Qt.CheckState.Unchecked
        assert test_item.foreground(0).color().name() == "#666666"

        # when
        with qtbot.waitSignal(tree_widget.itemChanged):
            test_item.setCheckState(0, Qt.CheckState.Checked)

        # then
        assert test_item.checkState(0) == Qt.CheckState.Checked
        assert test_item.foreground(0).color().name() == "#000000"
