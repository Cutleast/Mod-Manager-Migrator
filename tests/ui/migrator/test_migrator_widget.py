"""
Copyright (c) Cutleast
"""

from pathlib import Path
from typing import Any, Optional

import pytest
from pyfakefs.fake_filesystem import FakeFilesystem
from PySide6.QtWidgets import QComboBox, QLineEdit, QPushButton
from pytestqt.qtbot import QtBot
from setup.mock_plyvel import MockPlyvelDB
from utils import Utils

from core.config.app_config import AppConfig
from core.game.game import Game
from core.instance.instance import Instance
from core.mod_manager.instance_info import InstanceInfo
from core.mod_manager.mod_manager import ModManager
from core.mod_manager.modorganizer.mo2_instance_info import MO2InstanceInfo
from core.mod_manager.modorganizer.modorganizer import ModOrganizer
from core.mod_manager.vortex.profile_info import ProfileInfo
from core.mod_manager.vortex.vortex import Vortex
from ui.migrator.instance_creator.base_creator_widget import BaseCreatorWidget
from ui.migrator.instance_creator.instance_creator_widget import InstanceCreatorWidget
from ui.migrator.instance_creator.vortex_creator_widget import VortexCreatorWidget
from ui.migrator.instance_selector import VortexSelectorWidget
from ui.migrator.instance_selector.base_selector_widget import BaseSelectorWidget
from ui.migrator.instance_selector.instance_selector_widget import (
    InstanceSelectorWidget,
)
from ui.migrator.instance_selector.modorganizer_selector_widget import (
    ModOrganizerSelectorWidget,
)
from ui.migrator.migrator_widget import MigratorWidget
from ui.widgets.browse_edit import BrowseLineEdit

from ..ui_test import UiTest


class TestMigratorWidget(UiTest):
    """
    Tests `ui.migrator.migrator_widget.MigratorWidget`.
    """

    GAME_DROPDOWN: tuple[str, type[QComboBox]] = ("game_dropdown", QComboBox)
    """Identifier for accessing the private game_dropdown field."""

    SRC_SELECTOR: tuple[str, type[InstanceSelectorWidget]] = (
        "src_selector",
        InstanceSelectorWidget,
    )
    """Identifier for accessing the private src_selector field."""

    MOD_MANAGER_DROPDOWN: tuple[str, type[QComboBox]] = (
        "mod_manager_dropdown",
        QComboBox,
    )
    """
    Identifier for accessing the private mod_manager_dropdown field of InstanceSelector
    and InstanceCreator.
    """

    SRC_MOD_MANAGERS: tuple[str, type[dict[ModManager, BaseSelectorWidget]]] = (
        "mod_managers",
        dict,
    )
    """Identifier for accessing the private mod_managers field of InstanceSelector."""

    LOAD_SRC_BUTTON: tuple[str, type[QPushButton]] = ("load_src_button", QPushButton)
    """Identifier for accessing the private load_src_button field."""

    DST_CREATOR: tuple[str, type[InstanceCreatorWidget]] = (
        "dst_creator",
        InstanceCreatorWidget,
    )
    """Identifier for accessing the private dst_creator field."""

    DST_MOD_MANAGERS: tuple[str, type[dict[ModManager, BaseCreatorWidget]]] = (
        "mod_managers",
        dict,
    )
    """Identifier for accessing the private mod_managers field of InstanceCreator."""

    MIGRATE_BUTTON: tuple[str, type[QPushButton]] = ("migrate_button", QPushButton)
    """Identifier for accessing the private migrate_button field."""

    @pytest.fixture
    def widget(self, app_config: AppConfig, qtbot: QtBot) -> MigratorWidget:
        """
        Creates an instance of the MigratorWidget to test.

        Returns:
            MigratorWidget: A new MigratorWidget instance
        """

        return MigratorWidget(app_config)

    def test_initial_state(self, widget: MigratorWidget) -> None:
        """
        Tests the initial state of the MigratorWidget.

        Args:
            widget (MigratorWidget): MigratorWidget instance
        """

        # given
        game_dropdown: QComboBox = Utils.get_private_field(
            widget, *TestMigratorWidget.GAME_DROPDOWN
        )
        src_selector: InstanceSelectorWidget = Utils.get_private_field(
            widget, *TestMigratorWidget.SRC_SELECTOR
        )
        load_src_button: QPushButton = Utils.get_private_field(
            widget, *TestMigratorWidget.LOAD_SRC_BUTTON
        )
        dst_creator: InstanceCreatorWidget = Utils.get_private_field(
            widget, *TestMigratorWidget.DST_CREATOR
        )
        dst_mod_manager_dropdown: QComboBox = Utils.get_private_field(
            dst_creator, *TestMigratorWidget.MOD_MANAGER_DROPDOWN
        )
        migrate_button: QPushButton = Utils.get_private_field(
            widget, *TestMigratorWidget.MIGRATE_BUTTON
        )

        # then
        assert game_dropdown.currentIndex() == 0
        assert game_dropdown.isEnabled()
        assert game_dropdown.count() == len(Game.get_supported_games()) + 1
        assert widget.get_selected_game() is None
        assert not src_selector.isEnabled()
        assert src_selector.get_selected_mod_manager() is None
        with pytest.raises(ValueError, match="No instance data selected."):
            src_selector.get_cur_instance_data()
        assert not load_src_button.isEnabled()

        assert not dst_mod_manager_dropdown.isEnabled()
        assert dst_creator.get_selected_mod_manager() is None
        assert not dst_creator.isEnabled()
        assert not migrate_button.isEnabled()

    def test_select_src_instance(
        self,
        widget: MigratorWidget,
        ui_test_fs: FakeFilesystem,
        instance: Instance,
        qtbot: QtBot,
    ) -> None:
        """
        Tests the selection of a game, source mod manager and instance.
        """

        # given
        skyrimse: Game = Game.get_game_by_id("skyrimse")
        game_dropdown: QComboBox = Utils.get_private_field(
            widget, *TestMigratorWidget.GAME_DROPDOWN
        )
        src_selector: InstanceSelectorWidget = Utils.get_private_field(
            widget, *TestMigratorWidget.SRC_SELECTOR
        )
        src_mod_manager_dropdown: QComboBox = Utils.get_private_field(
            src_selector, *TestMigratorWidget.MOD_MANAGER_DROPDOWN
        )
        src_mod_managers: dict[ModManager, BaseSelectorWidget] = (
            Utils.get_private_field(src_selector, *TestMigratorWidget.SRC_MOD_MANAGERS)
        )
        load_src_button: QPushButton = Utils.get_private_field(
            widget, *TestMigratorWidget.LOAD_SRC_BUTTON
        )
        dst_creator: InstanceCreatorWidget = Utils.get_private_field(
            widget, *TestMigratorWidget.DST_CREATOR
        )

        # when
        game_dropdown.setCurrentText(skyrimse.display_name)

        # then
        assert widget.get_selected_game() is skyrimse
        assert src_mod_manager_dropdown.isEnabled()
        assert not dst_creator.isEnabled()

        # when
        src_mod_manager_dropdown.setCurrentText(ModOrganizer.get_display_name())

        # then
        cur_mod_manager: Optional[ModManager] = src_selector.get_selected_mod_manager()
        assert isinstance(cur_mod_manager, ModOrganizer)

        # when
        mo2_selector_widget: BaseSelectorWidget = src_mod_managers[cur_mod_manager]

        # then
        assert isinstance(mo2_selector_widget, ModOrganizerSelectorWidget)

        # when
        Utils.get_private_field(
            mo2_selector_widget, "instance_dropdown", QComboBox
        ).setCurrentText("Portable")
        Utils.get_private_field(
            mo2_selector_widget, "portable_path_entry", BrowseLineEdit
        ).setText("C:\\Modding\\Test Instance")
        Utils.get_private_field(
            mo2_selector_widget, "profile_dropdown", QComboBox
        ).setCurrentText("Default")

        # then
        assert load_src_button.isEnabled()

        # when
        with qtbot.waitSignal(widget.src_selected, timeout=10_000) as signal:
            load_src_button.click()

        # then
        assert signal.args is not None
        src_instance: Optional[Any] = signal.args[0]
        assert isinstance(src_instance, Instance)
        assert src_instance.mods == instance.mods
        assert not load_src_button.isEnabled()
        assert dst_creator.isEnabled()

        # when
        src_instance = widget.get_src_instance()
        src_instance_info: Optional[InstanceInfo] = widget.get_src_instance_info()

        # then
        assert src_instance is not None
        assert isinstance(src_instance_info, MO2InstanceInfo)
        assert src_instance_info == MO2InstanceInfo(
            display_name="Portable",
            game=skyrimse,
            profile="Default",
            is_global=False,
            base_folder=Path("C:\\Modding\\Test Instance"),
            mods_folder=Path("C:\\Modding\\Test Instance\\mods"),
            profiles_folder=Path("C:\\Modding\\Test Instance\\profiles"),
        )

    def test_change_src_instance(
        self,
        widget: MigratorWidget,
        ui_test_fs: FakeFilesystem,
        full_vortex_db: MockPlyvelDB,
        vortex_profile_info: ProfileInfo,
        instance: Instance,
        qtbot: QtBot,
    ) -> None:
        """
        Tests the selection of another instance after loading the first one.
        """

        self.test_select_src_instance(widget, ui_test_fs, instance, qtbot)

        # given
        skyrimse: Game = Game.get_game_by_id("skyrimse")
        game_dropdown: QComboBox = Utils.get_private_field(
            widget, *TestMigratorWidget.GAME_DROPDOWN
        )
        src_selector: InstanceSelectorWidget = Utils.get_private_field(
            widget, *TestMigratorWidget.SRC_SELECTOR
        )
        src_mod_manager_dropdown: QComboBox = Utils.get_private_field(
            src_selector, *TestMigratorWidget.MOD_MANAGER_DROPDOWN
        )
        src_mod_managers: dict[ModManager, BaseSelectorWidget] = (
            Utils.get_private_field(src_selector, *TestMigratorWidget.SRC_MOD_MANAGERS)
        )
        vortex: Vortex = {m.get_id(): m for m in src_mod_managers}[Vortex.get_id()]  # type: ignore
        vortex.db_path.mkdir(parents=True, exist_ok=True)
        load_src_button: QPushButton = Utils.get_private_field(
            widget, *TestMigratorWidget.LOAD_SRC_BUTTON
        )

        # when
        game_dropdown.setCurrentIndex(0)  # unselect game

        # then
        assert widget.get_selected_game() is None
        assert widget.get_src_instance() is None
        with pytest.raises(ValueError):
            widget.get_src_instance_info()
        assert not src_mod_manager_dropdown.isEnabled()
        assert src_mod_manager_dropdown.currentIndex() == 0
        assert not src_selector.isEnabled()
        assert not load_src_button.isEnabled()

        # when
        game_dropdown.setCurrentText(skyrimse.display_name)

        # then
        assert src_mod_manager_dropdown.isEnabled()

        # when
        src_mod_manager_dropdown.setCurrentText(Vortex.get_display_name())

        # then
        cur_mod_manager: Optional[ModManager] = src_selector.get_selected_mod_manager()
        assert isinstance(cur_mod_manager, Vortex)

        # when
        vortex_selector_widget: BaseSelectorWidget = src_mod_managers[cur_mod_manager]

        # then
        assert isinstance(vortex_selector_widget, VortexSelectorWidget)

        # when
        profile_dropdown: QComboBox = Utils.get_private_field(
            vortex_selector_widget, "profile_dropdown", QComboBox
        )

        # then
        assert profile_dropdown.count() == 3
        assert profile_dropdown.itemText(2) == vortex_profile_info.display_name

        # when
        profile_dropdown.setCurrentIndex(2)

        # then
        assert load_src_button.isEnabled()

        # when
        with qtbot.waitSignal(widget.src_selected, timeout=10_000) as signal:
            load_src_button.click()

        # then
        assert signal.args is not None
        src_instance: Optional[Any] = signal.args[0]
        assert isinstance(src_instance, Instance)

        # when
        src_instance = widget.get_src_instance()
        src_instance_info: Optional[InstanceInfo] = widget.get_src_instance_info()

        # then
        assert src_instance is not None
        assert isinstance(src_instance_info, ProfileInfo)
        assert src_instance_info == vortex_profile_info

    def test_create_dst_instance(
        self,
        widget: MigratorWidget,
        ui_test_fs: FakeFilesystem,
        ready_vortex_db: MockPlyvelDB,
        instance: Instance,
        qtbot: QtBot,
    ) -> None:
        """
        Tests the creation of the destination instance after loading the source instance.
        """

        self.test_select_src_instance(widget, ui_test_fs, instance, qtbot)

        # given
        dst_creator: InstanceCreatorWidget = Utils.get_private_field(
            widget, *TestMigratorWidget.DST_CREATOR
        )
        dst_mod_manager_dropdown: QComboBox = Utils.get_private_field(
            dst_creator, *TestMigratorWidget.MOD_MANAGER_DROPDOWN
        )
        dst_mod_managers: dict[ModManager, BaseCreatorWidget] = Utils.get_private_field(
            dst_creator, *TestMigratorWidget.DST_MOD_MANAGERS
        )
        vortex: Vortex = {m.get_id(): m for m in dst_mod_managers}[Vortex.get_id()]  # type: ignore
        vortex.db_path.mkdir(parents=True, exist_ok=True)
        migrate_button: QPushButton = Utils.get_private_field(
            widget, *TestMigratorWidget.MIGRATE_BUTTON
        )

        # then
        assert dst_creator.isEnabled()
        assert dst_mod_manager_dropdown.isEnabled()
        assert dst_creator.get_selected_mod_manager() is None
        assert not migrate_button.isEnabled()

        # when
        dst_mod_manager_dropdown.setCurrentText(Vortex.get_display_name())

        # then
        assert dst_creator.get_selected_mod_manager() is vortex

        # when
        vortex_creator_widget: BaseCreatorWidget = dst_mod_managers[vortex]

        # then
        assert isinstance(vortex_creator_widget, VortexCreatorWidget)

        # when
        Utils.get_private_field(
            vortex_creator_widget, "profile_name_entry", QLineEdit
        ).setText("test")

        # then
        assert vortex_creator_widget.validate()
        assert migrate_button.isEnabled()

        # when
        profile: ProfileInfo = vortex_creator_widget.get_instance(
            Game.get_game_by_id("skyrimse")
        )

        # then
        assert profile.display_name.startswith("test")

        # when/then
        with qtbot.waitSignal(widget.migration_started):
            migrate_button.click()
