"""
Copyright (c) Cutleast
"""

from typing import Optional

import qtawesome as qta
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget

from app_context import AppContext
from core.game.game import Game
from core.instance.instance import Instance
from core.mod_manager.instance_info import InstanceInfo
from core.mod_manager.mod_manager import ModManager
from ui.widgets.smooth_scroll_area import SmoothScrollArea

from .instance_creator.instance_creator import InstanceCreator
from .instance_selector.instance_selector import InstanceSelector


class MigratorWidget(SmoothScrollArea):
    """
    Widget for configuring and starting the migration process.
    """

    src_selected = Signal(Instance)
    """This signal gets emitted when the source instance is selected."""

    migration_started = Signal()
    """This signal gets emitted when the user clicks on the migrate button."""

    __vlayout: QVBoxLayout

    __src_selector: InstanceSelector
    __dst_creator: InstanceCreator

    __migrate_button: QPushButton

    def __init__(self) -> None:
        super().__init__()

        self.__init_ui()

        self.__migrate_button.clicked.connect(AppContext.get_app().migrate)
        self.__src_selector.instance_selected.connect(self.src_selected)
        self.__dst_creator.instance_valid.connect(self.__migrate_button.setEnabled)

    def __init_ui(self) -> None:
        scroll_widget = QWidget()
        self.setWidget(scroll_widget)

        self.__vlayout = QVBoxLayout()
        scroll_widget.setLayout(self.__vlayout)

        self.__init_src_selector()

        self.__vlayout.addStretch()

        arrow_down_icon = QLabel()
        arrow_down_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        arrow_down_icon.setPixmap(
            qta.icon(
                "mdi6.chevron-down", color=self.palette().text().color(), scale_factor=2
            ).pixmap(96, 96)
        )
        self.__vlayout.addWidget(arrow_down_icon)

        self.__vlayout.addStretch()

        self.__init_dst_creator()
        self.__init_footer()

    def __init_src_selector(self) -> None:
        title_label = QLabel(self.tr("Choose the source instance:"))
        title_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        title_label.setObjectName("h3")
        self.__vlayout.addWidget(title_label, 0, Qt.AlignmentFlag.AlignHCenter)
        self.__vlayout.addSpacing(15)

        self.__src_selector = InstanceSelector()
        self.__vlayout.addWidget(self.__src_selector)

    def __init_dst_creator(self) -> None:
        title_label = QLabel(self.tr("Configure the destination instance:"))
        title_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        title_label.setObjectName("h3")
        self.__vlayout.addWidget(title_label, 0, Qt.AlignmentFlag.AlignHCenter)
        self.__vlayout.addSpacing(15)

        self.__dst_creator = InstanceCreator()
        self.__vlayout.addWidget(self.__dst_creator)

    def __init_footer(self) -> None:
        self.__migrate_button = QPushButton(self.tr("Migrate..."))
        self.__migrate_button.setEnabled(False)
        self.__migrate_button.setObjectName("primary")
        self.__vlayout.addWidget(self.__migrate_button)

    def get_selected_game(self) -> Optional[Game]:
        """
        Returns the currently selected game.

        Returns:
            Optional[Game]: The game
        """

        return self.__src_selector.get_cur_game()

    def get_src_mod_manager(self) -> Optional[ModManager]:
        """
        Returns the mod manager of the selected source instance.

        Returns:
            Optional[ModManager]: The mod manager
        """

        return self.__src_selector.get_selected_mod_manager()

    def get_src_instance_info(self) -> Optional[InstanceInfo]:
        """
        Returns the instance data for the selected source instance.

        Returns:
            Optional[InstanceInfo]: The instance data
        """

        return self.__src_selector.get_cur_instance_data()

    def get_src_instance(self) -> Optional[Instance]:
        """
        Returns the loaded instance for the currently selected source instance data.

        Returns:
            Optional[Instance]: The instance
        """

        return self.__src_selector.get_cur_mod_instance()

    def get_dst_mod_manager(self) -> Optional[ModManager]:
        """
        Returns the mod manager of the selected or configured destination instance.

        Returns:
            Optional[ModManager]: The mod manager
        """

        return self.__dst_creator.get_selected_mod_manager()

    def get_dst_instance_info(self, game: Game) -> Optional[InstanceInfo]:
        """
        Returns the instance data for the selected or configured destination instance.

        Args:
            game (Game): The selected game

        Returns:
            Optional[InstanceInfo]: The instance data
        """

        return self.__dst_creator.get_instance_data(game)
