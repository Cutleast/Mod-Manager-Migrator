"""
Copyright (c) Cutleast
"""

import os
from typing import Any, Optional

import pytest
from PySide6.QtWidgets import QLineEdit, QRadioButton
from pytestqt.qtbot import QtBot

from core.utilities.env_resolver import resolve
from ui.instance_creator.modorganizer import ModOrganizerWidget

os.environ["QT_QPA_PLATFORM"] = "offscreen"  # render widgets off-screen


class TestModOrganizerWidget:
    """
    Tests `ui.instance_creator.modorganizer.ModOrganizerWidget`.
    """

    NAME_ENTRY_ID: str = "_ModOrganizerWidget__instance_name_entry"
    INSTANCE_PATH_ENTRY_ID: str = "_ModOrganizerWidget__instance_path_entry"
    MODS_PATH_ENTRY_ID: str = "_ModOrganizerWidget__mods_path_entry"
    USE_PORTABLE_ID: str = "_ModOrganizerWidget__use_portable"
    USE_GLOBAL_ID: str = "_ModOrganizerWidget__use_global"
    INSTALL_MO2_ID: str = "_ModOrganizerWidget__install_mo2"
    USE_ROOT_BUILDER_ID: str = "_ModOrganizerWidget__use_root_builder"

    @pytest.fixture
    def widget(self, qtbot: QtBot) -> ModOrganizerWidget:
        """
        Fixture to create and provide a ModOrganizerWidget instance for tests.
        """

        mo2_widget = ModOrganizerWidget()
        qtbot.addWidget(mo2_widget)
        mo2_widget.show()
        return mo2_widget

    def get_name_entry(self, widget: ModOrganizerWidget) -> QLineEdit:
        name_entry: Optional[Any] = getattr(
            widget, TestModOrganizerWidget.NAME_ENTRY_ID, None
        )

        if name_entry is None:
            raise ValueError("Name entry not found!")
        elif not isinstance(name_entry, QLineEdit):
            raise TypeError("Name entry is not a QLineEdit!")

        return name_entry

    def get_instance_path_entry(self, widget: ModOrganizerWidget) -> QLineEdit:
        instance_path_entry: Optional[Any] = getattr(
            widget, TestModOrganizerWidget.INSTANCE_PATH_ENTRY_ID, None
        )

        if instance_path_entry is None:
            raise ValueError("Instance path entry not found!")
        elif not isinstance(instance_path_entry, QLineEdit):
            raise TypeError("Instance path entry is not a QLineEdit!")

        return instance_path_entry

    def get_mods_path_entry(self, widget: ModOrganizerWidget) -> QLineEdit:
        mods_path_entry: Optional[Any] = getattr(
            widget, TestModOrganizerWidget.MODS_PATH_ENTRY_ID, None
        )

        if mods_path_entry is None:
            raise ValueError("Mods path entry not found!")
        elif not isinstance(mods_path_entry, QLineEdit):
            raise TypeError("Mods path entry is not a QLineEdit!")

        return mods_path_entry

    def get_use_portable(self, widget: ModOrganizerWidget) -> QRadioButton:
        use_portable: Optional[Any] = getattr(
            widget, TestModOrganizerWidget.USE_PORTABLE_ID, None
        )

        if use_portable is None:
            raise ValueError("Use portable radiobutton not found!")
        elif not isinstance(use_portable, QRadioButton):
            raise TypeError("Use portable radiobutton is not a QRadioButton!")

        return use_portable

    def get_use_global(self, widget: ModOrganizerWidget) -> QRadioButton:
        use_global: Optional[Any] = getattr(
            widget, TestModOrganizerWidget.USE_GLOBAL_ID, None
        )

        if use_global is None:
            raise ValueError("Use global radiobutton not found!")
        elif not isinstance(use_global, QRadioButton):
            raise TypeError("Use global radiobutton is not a QRadioButton!")

        return use_global

    def assert_initial_state(self, widget: ModOrganizerWidget) -> None:
        """
        Asserts the initial state of the widget.
        """

        name_entry: QLineEdit = self.get_name_entry(widget)
        instance_path_entry: QLineEdit = self.get_instance_path_entry(widget)
        mods_path_entry: QLineEdit = self.get_mods_path_entry(widget)
        use_portable: QRadioButton = self.get_use_portable(widget)
        use_global: QRadioButton = self.get_use_global(widget)

        assert name_entry.text() == ""
        assert name_entry.isEnabled()
        assert instance_path_entry.text() == resolve("%LOCALAPPDATA%\\ModOrganizer\\")
        assert not instance_path_entry.isEnabled()
        assert mods_path_entry.text() == resolve("%LOCALAPPDATA%\\ModOrganizer\\\\mods")
        assert mods_path_entry.isEnabled()
        assert not use_portable.isChecked()
        assert use_global.isChecked()

    def assert_global_state(self, widget: ModOrganizerWidget) -> None:
        """
        Asserts state right after the global radiobutton was checked.
        """

        name_entry: QLineEdit = self.get_name_entry(widget)
        instance_path_entry: QLineEdit = self.get_instance_path_entry(widget)
        mods_path_entry: QLineEdit = self.get_mods_path_entry(widget)
        use_portable: QRadioButton = self.get_use_portable(widget)
        use_global: QRadioButton = self.get_use_global(widget)

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

    def assert_portable_state(self, widget: ModOrganizerWidget) -> None:
        """
        Asserts state right after the portable radiobutton was checked.
        """

        instance_path_entry: QLineEdit = self.get_instance_path_entry(widget)
        mods_path_entry: QLineEdit = self.get_mods_path_entry(widget)
        use_portable: QRadioButton = self.get_use_portable(widget)
        use_global: QRadioButton = self.get_use_global(widget)

        assert instance_path_entry.text() == ""
        assert instance_path_entry.isEnabled()
        assert mods_path_entry.text() == ""
        assert mods_path_entry.isEnabled()
        assert use_portable.isChecked()
        assert not use_global.isChecked()

    def test_initial_state(self, widget: ModOrganizerWidget) -> None:
        """
        Tests the initial state of the widget.
        """

        self.assert_initial_state(widget)

    def test_on_name_change(self, widget: ModOrganizerWidget) -> None:
        """
        Tests `ui.instance_creator.modorganizer.ModOrganizerWidget.__on_name_change()`.
        """

        # given
        name_entry: QLineEdit = self.get_name_entry(widget)
        instance_path_entry: QLineEdit = self.get_instance_path_entry(widget)
        mods_path_entry: QLineEdit = self.get_mods_path_entry(widget)
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

    def test_on_path_change(self, widget: ModOrganizerWidget) -> None:
        """
        Tests `ui.instance_creator.modorganizer.ModOrganizerWidget.__on_path_change()`.
        """

        # given
        instance_path_entry: QLineEdit = self.get_instance_path_entry(widget)
        mods_path_entry: QLineEdit = self.get_mods_path_entry(widget)
        use_portable: QRadioButton = self.get_use_portable(widget)
        new_path: str = "New Path"

        # when
        use_portable.setChecked(True)
        self.assert_portable_state(widget)
        instance_path_entry.setText(new_path)

        # then
        assert instance_path_entry.text() == new_path
        assert mods_path_entry.text() == new_path + "\\mods"

    def test_on_path_change_relative(self, widget: ModOrganizerWidget) -> None:
        """
        Tests `ui.instance_creator.modorganizer.ModOrganizerWidget.__on_path_change()`
        with a preinserted mods folder relative to the instance path.
        """

        # given
        instance_path_entry: QLineEdit = self.get_instance_path_entry(widget)
        mods_path_entry: QLineEdit = self.get_mods_path_entry(widget)
        use_portable: QRadioButton = self.get_use_portable(widget)
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

    def test_on_path_change_independent(self, widget: ModOrganizerWidget) -> None:
        """
        Tests `ui.instance_creator.modorganizer.ModOrganizerWidget.__on_path_change()`
        with a preinserted mods folder independent from the instance path.
        """

        # given
        instance_path_entry: QLineEdit = self.get_instance_path_entry(widget)
        mods_path_entry: QLineEdit = self.get_mods_path_entry(widget)
        use_portable: QRadioButton = self.get_use_portable(widget)
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

    def test_on_global_toggled(self, widget: ModOrganizerWidget) -> None:
        """
        Tests `ui.instance_creator.modorganizer.ModOrganizerWidget.__on_global_toggled()`.
        """

        # given
        name_entry: QLineEdit = self.get_name_entry(widget)
        use_portable: QRadioButton = self.get_use_portable(widget)
        use_global: QRadioButton = self.get_use_global(widget)

        # when
        use_portable.setChecked(True)

        # then
        self.assert_portable_state(widget)

        # when
        name_entry.setText("Test")
        use_global.setChecked(True)

        # then
        self.assert_global_state(widget)
