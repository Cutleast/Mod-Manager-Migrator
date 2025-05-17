"""
Copyright (c) Cutleast
"""

import pytest
from pyfakefs.fake_filesystem import FakeFilesystem
from PySide6.QtWidgets import QComboBox
from pytestqt.qtbot import QtBot

from core.game.game import Game
from core.mod_manager.modorganizer.modorganizer import ModOrganizer
from tests.ui.ui_test import UiTest
from tests.utils import Utils
from ui.migrator.instance_selector.modorganizer_selector_widget import (
    ModOrganizerSelectorWidget,
)
from ui.widgets.browse_edit import BrowseLineEdit


class TestModOrganizerSelectorWidget(UiTest):
    """
    Tests `ModOrganizerSelectorWidget`.
    """

    INSTANCE_DROPDOWN: tuple[str, type[QComboBox]] = ("instance_dropdown", QComboBox)
    """Identifier for accessing the private instance_dropdown field."""

    PORTABLE_PATH_ENTRY: tuple[str, type[BrowseLineEdit]] = (
        "portable_path_entry",
        BrowseLineEdit,
    )
    """Identifier for accessing the private portable_path_entry field."""

    PROFILE_DROPDOWN: tuple[str, type[QComboBox]] = ("profile_dropdown", QComboBox)
    """Identifier for accessing the private profile_dropdown field."""

    @pytest.fixture
    def widget(
        self, ui_test_fs: FakeFilesystem, qtbot: QtBot
    ) -> ModOrganizerSelectorWidget:
        """
        Fixture to create and provide a ModOrganizerSelectorWidget instance for tests.
        """

        mo2_widget = ModOrganizerSelectorWidget(
            ModOrganizer().get_instance_names(Game.get_game_by_id("skyrimse"))
        )
        qtbot.addWidget(mo2_widget)
        mo2_widget.show()
        return mo2_widget

    def assert_initial_state(self, widget: ModOrganizerSelectorWidget) -> None:
        """
        Asserts the initial state of the widget.
        """

        instance_dropdown: QComboBox = Utils.get_private_field(
            widget, *TestModOrganizerSelectorWidget.INSTANCE_DROPDOWN
        )
        portable_path_entry: BrowseLineEdit = Utils.get_private_field(
            widget, *TestModOrganizerSelectorWidget.PORTABLE_PATH_ENTRY
        )
        profile_dropdown: QComboBox = Utils.get_private_field(
            widget, *TestModOrganizerSelectorWidget.PROFILE_DROPDOWN
        )

        assert instance_dropdown.currentIndex() == 0
        assert instance_dropdown.isEnabled()
        assert portable_path_entry.text() == ""
        assert not portable_path_entry.isEnabled()
        assert profile_dropdown.currentIndex() == 0
        assert not profile_dropdown.isEnabled()
        assert not widget.validate()

    def test_initial_state(self, widget: ModOrganizerSelectorWidget) -> None:
        """
        Tests the initial state of the widget.
        """

        self.assert_initial_state(widget)

    def test_select_global_instance(
        self, ui_test_fs: FakeFilesystem, widget: ModOrganizerSelectorWidget
    ) -> None:
        """
        Tests the selection of a global instance.
        """

        # given
        instance_dropdown: QComboBox = Utils.get_private_field(
            widget, *TestModOrganizerSelectorWidget.INSTANCE_DROPDOWN
        )
        portable_path_entry: BrowseLineEdit = Utils.get_private_field(
            widget, *TestModOrganizerSelectorWidget.PORTABLE_PATH_ENTRY
        )
        profile_dropdown: QComboBox = Utils.get_private_field(
            widget, *TestModOrganizerSelectorWidget.PROFILE_DROPDOWN
        )

        # then
        assert instance_dropdown.count() == 3
        assert instance_dropdown.itemText(1) == "Test Instance"

        # when
        instance_dropdown.setCurrentIndex(1)

        # then
        assert not portable_path_entry.isEnabled()
        assert profile_dropdown.isEnabled()
        assert profile_dropdown.count() == 3
        assert profile_dropdown.itemText(1) == "Default"
        assert profile_dropdown.itemText(2) == "TestProfile"
        assert not widget.validate()

        # when
        profile_dropdown.setCurrentIndex(2)

        # then
        assert widget.validate()
