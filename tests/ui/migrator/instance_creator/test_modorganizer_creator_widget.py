"""
Copyright (c) Cutleast
"""

import os

import pytest
from PySide6.QtWidgets import QCheckBox, QLineEdit, QRadioButton
from pytestqt.qtbot import QtBot
from utils import Utils

from core.utilities.env_resolver import resolve
from tests.ui.ui_test import UiTest
from ui.migrator.instance_creator.modorganizer_creator_widget import (
    ModOrganizerCreatorWidget,
)

os.environ["QT_QPA_PLATFORM"] = "offscreen"  # render widgets off-screen


class TestModOrganizerCreatorWidget(UiTest):
    """
    Tests `ModOrganizerCreatorWidget`.
    """

    NAME_ENTRY: tuple[str, type[QLineEdit]] = ("instance_name_entry", QLineEdit)
    """Identifier for accessing the private instance_name_entry field."""

    INSTANCE_PATH_ENTRY: tuple[str, type[QLineEdit]] = (
        "instance_path_entry",
        QLineEdit,
    )
    """Identifier for accessing the private instance_path_entry field."""

    MODS_PATH_ENTRY: tuple[str, type[QLineEdit]] = ("mods_path_entry", QLineEdit)
    """Identifier for accessing the private mods_path_entry field."""

    USE_PORTABLE: tuple[str, type[QRadioButton]] = ("use_portable", QRadioButton)
    """Identifier for accessing the private use_portable field."""

    USE_GLOBAL: tuple[str, type[QRadioButton]] = ("use_global", QRadioButton)
    """Identifier for accessing the private use_global field."""

    INSTALL_MO2: tuple[str, type[QCheckBox]] = ("install_mo2", QCheckBox)
    """Identifier for accessing the private install_mo2 field."""

    USE_ROOT_BUILDER: tuple[str, type[QCheckBox]] = ("use_root_builder", QCheckBox)
    """Identifier for accessing the private use_root_builder field."""

    @pytest.fixture
    def widget(self, qtbot: QtBot) -> ModOrganizerCreatorWidget:
        """
        Fixture to create and provide a ModOrganizerWidget instance for tests.
        """

        mo2_widget = ModOrganizerCreatorWidget()
        qtbot.addWidget(mo2_widget)
        mo2_widget.show()
        return mo2_widget

    def assert_initial_state(self, widget: ModOrganizerCreatorWidget) -> None:
        """
        Asserts the initial state of the widget.
        """

        name_entry: QLineEdit = Utils.get_private_field(
            widget, *TestModOrganizerCreatorWidget.NAME_ENTRY
        )
        instance_path_entry: QLineEdit = Utils.get_private_field(
            widget, *TestModOrganizerCreatorWidget.INSTANCE_PATH_ENTRY
        )
        mods_path_entry: QLineEdit = Utils.get_private_field(
            widget, *TestModOrganizerCreatorWidget.MODS_PATH_ENTRY
        )
        use_portable: QRadioButton = Utils.get_private_field(
            widget, *TestModOrganizerCreatorWidget.USE_PORTABLE
        )
        use_global: QRadioButton = Utils.get_private_field(
            widget, *TestModOrganizerCreatorWidget.USE_GLOBAL
        )

        assert name_entry.text() == ""
        assert name_entry.isEnabled()
        assert instance_path_entry.text() == resolve("%LOCALAPPDATA%\\ModOrganizer\\")
        assert not instance_path_entry.isEnabled()
        assert mods_path_entry.text() == resolve("%LOCALAPPDATA%\\ModOrganizer\\\\mods")
        assert mods_path_entry.isEnabled()
        assert not use_portable.isChecked()
        assert use_global.isChecked()

    def assert_global_state(self, widget: ModOrganizerCreatorWidget) -> None:
        """
        Asserts state right after the global radiobutton was checked.
        """

        name_entry: QLineEdit = Utils.get_private_field(
            widget, *TestModOrganizerCreatorWidget.NAME_ENTRY
        )
        instance_path_entry: QLineEdit = Utils.get_private_field(
            widget, *TestModOrganizerCreatorWidget.INSTANCE_PATH_ENTRY
        )
        mods_path_entry: QLineEdit = Utils.get_private_field(
            widget, *TestModOrganizerCreatorWidget.MODS_PATH_ENTRY
        )
        use_portable: QRadioButton = Utils.get_private_field(
            widget, *TestModOrganizerCreatorWidget.USE_PORTABLE
        )
        use_global: QRadioButton = Utils.get_private_field(
            widget, *TestModOrganizerCreatorWidget.USE_GLOBAL
        )

        assert (
            instance_path_entry.text()
            == resolve("%LOCALAPPDATA%\\ModOrganizer\\") + name_entry.text()
        )
        assert not instance_path_entry.isEnabled()
        assert (
            mods_path_entry.text()
            == resolve("%LOCALAPPDATA%\\ModOrganizer\\") + name_entry.text() + "\\mods"
        )
        assert mods_path_entry.isEnabled()
        assert not use_portable.isChecked()
        assert use_global.isChecked()

    def assert_portable_state(self, widget: ModOrganizerCreatorWidget) -> None:
        """
        Asserts state right after the portable radiobutton was checked.
        """

        instance_path_entry: QLineEdit = Utils.get_private_field(
            widget, *TestModOrganizerCreatorWidget.INSTANCE_PATH_ENTRY
        )
        mods_path_entry: QLineEdit = Utils.get_private_field(
            widget, *TestModOrganizerCreatorWidget.MODS_PATH_ENTRY
        )
        use_portable: QRadioButton = Utils.get_private_field(
            widget, *TestModOrganizerCreatorWidget.USE_PORTABLE
        )
        use_global: QRadioButton = Utils.get_private_field(
            widget, *TestModOrganizerCreatorWidget.USE_GLOBAL
        )

        assert instance_path_entry.text() == ""
        assert instance_path_entry.isEnabled()
        assert mods_path_entry.text() == ""
        assert mods_path_entry.isEnabled()
        assert use_portable.isChecked()
        assert not use_global.isChecked()

    def test_initial_state(self, widget: ModOrganizerCreatorWidget) -> None:
        """
        Tests the initial state of the widget.
        """

        self.assert_initial_state(widget)

    def test_on_name_change(self, widget: ModOrganizerCreatorWidget) -> None:
        """
        Tests `ModOrganizerCreatorWidget.__on_name_change()`.
        """

        # given
        name_entry: QLineEdit = Utils.get_private_field(
            widget, *TestModOrganizerCreatorWidget.NAME_ENTRY
        )
        instance_path_entry: QLineEdit = Utils.get_private_field(
            widget, *TestModOrganizerCreatorWidget.INSTANCE_PATH_ENTRY
        )
        mods_path_entry: QLineEdit = Utils.get_private_field(
            widget, *TestModOrganizerCreatorWidget.MODS_PATH_ENTRY
        )
        new_name: str = "New Name"

        # when
        self.assert_initial_state(widget)
        name_entry.setText(new_name)

        # then
        assert (
            instance_path_entry.text()
            == resolve("%LOCALAPPDATA%\\ModOrganizer\\") + new_name
        )
        assert (
            mods_path_entry.text()
            == resolve("%LOCALAPPDATA%\\ModOrganizer\\") + new_name + "\\mods"
        )

    def test_on_path_change(self, widget: ModOrganizerCreatorWidget) -> None:
        """
        Tests `ModOrganizerCreatorWidget.__on_path_change()`.
        """

        # given
        instance_path_entry: QLineEdit = Utils.get_private_field(
            widget, *TestModOrganizerCreatorWidget.INSTANCE_PATH_ENTRY
        )
        mods_path_entry: QLineEdit = Utils.get_private_field(
            widget, *TestModOrganizerCreatorWidget.MODS_PATH_ENTRY
        )
        use_portable: QRadioButton = Utils.get_private_field(
            widget, *TestModOrganizerCreatorWidget.USE_PORTABLE
        )
        new_path: str = "New Path"

        # when
        use_portable.setChecked(True)
        self.assert_portable_state(widget)
        instance_path_entry.setText(new_path)

        # then
        assert instance_path_entry.text() == new_path
        assert mods_path_entry.text() == new_path + "\\mods"

    def test_on_path_change_relative(self, widget: ModOrganizerCreatorWidget) -> None:
        """
        Tests `ModOrganizerCreatorWidget.__on_path_change()` with a preinserted mods
        folder relative to the instance path.
        """

        # given
        instance_path_entry: QLineEdit = Utils.get_private_field(
            widget, *TestModOrganizerCreatorWidget.INSTANCE_PATH_ENTRY
        )
        mods_path_entry: QLineEdit = Utils.get_private_field(
            widget, *TestModOrganizerCreatorWidget.MODS_PATH_ENTRY
        )
        use_portable: QRadioButton = Utils.get_private_field(
            widget, *TestModOrganizerCreatorWidget.USE_PORTABLE
        )
        old_path: str = "Old Path"
        new_path: str = "New Path"

        # when
        use_portable.setChecked(True)
        self.assert_portable_state(widget)
        instance_path_entry.setText(old_path)
        mods_path_entry.setText(old_path + "\\mods")
        instance_path_entry.setText(new_path)

        # then
        assert instance_path_entry.text() == new_path
        assert mods_path_entry.text() == new_path + "\\mods"

    def test_on_path_change_independent(
        self, widget: ModOrganizerCreatorWidget
    ) -> None:
        """
        Tests `ModOrganizerCreatorWidget.__on_path_change()` with a preinserted mods
        folder independent from the instance path.
        """

        # given
        instance_path_entry: QLineEdit = Utils.get_private_field(
            widget, *TestModOrganizerCreatorWidget.INSTANCE_PATH_ENTRY
        )
        mods_path_entry: QLineEdit = Utils.get_private_field(
            widget, *TestModOrganizerCreatorWidget.MODS_PATH_ENTRY
        )
        use_portable: QRadioButton = Utils.get_private_field(
            widget, *TestModOrganizerCreatorWidget.USE_PORTABLE
        )
        old_path: str = "Old Path"
        new_path: str = "New Path"

        # when
        use_portable.setChecked(True)
        self.assert_portable_state(widget)
        instance_path_entry.setText(old_path)
        mods_path_entry.setText("mods")
        instance_path_entry.setText(new_path)

        # then
        assert instance_path_entry.text() == new_path
        assert mods_path_entry.text() == "mods"

    def test_on_global_toggled(self, widget: ModOrganizerCreatorWidget) -> None:
        """
        Tests `ModOrganizerCreatorWidget.__on_global_toggled()`.
        """

        # given
        name_entry: QLineEdit = Utils.get_private_field(
            widget, *TestModOrganizerCreatorWidget.NAME_ENTRY
        )
        use_portable: QRadioButton = Utils.get_private_field(
            widget, *TestModOrganizerCreatorWidget.USE_PORTABLE
        )
        use_global: QRadioButton = Utils.get_private_field(
            widget, *TestModOrganizerCreatorWidget.USE_GLOBAL
        )

        # when
        use_portable.setChecked(True)

        # then
        self.assert_portable_state(widget)

        # when
        name_entry.setText("Test")
        use_global.setChecked(True)

        # then
        self.assert_global_state(widget)
