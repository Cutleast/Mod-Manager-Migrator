"""
Copyright (c) Cutleast
"""

from typing import Optional, override

from PySide6.QtCore import QEvent, QObject, Qt, Signal
from PySide6.QtGui import QIcon, QWheelEvent
from PySide6.QtWidgets import (
    QComboBox,
    QGridLayout,
    QLabel,
    QSpinBox,
    QStackedLayout,
    QVBoxLayout,
    QWidget,
)

from core.game.game import Game
from core.mod_manager import MOD_MANAGERS
from core.mod_manager.instance_info import InstanceInfo
from core.mod_manager.mod_manager import ModManager

from . import INSTANCE_WIDGETS
from .base_selector_widget import BaseSelectorWidget


class InstanceSelectorWidget(QWidget):
    """
    Widget for selecting the source instance.
    """

    instance_valid = Signal(bool)
    """
    This signal is emitted when the validation status of the selected instance changes.
    """

    changed = Signal()
    """
    This signal is emitted everytime the user changes something at the selection.
    """

    __cur_game: Optional[Game] = None
    """
    Currently selected game.
    """

    __cur_instance_data: Optional[InstanceInfo] = None
    """
    Currently selected instance data.
    """

    __cur_mod_manager: Optional[ModManager] = None
    """
    Currently selected mod manager.
    """

    __mod_managers: dict[ModManager, BaseSelectorWidget]
    """
    Maps mod managers to their corresponding instance widgets.
    """

    __vlayout: QVBoxLayout
    __mod_manager_dropdown: QComboBox
    __instance_stack_layout: QStackedLayout
    __placeholder_widget: QWidget

    def __init__(self) -> None:
        super().__init__()

        self.__init_ui()

    def __init_ui(self) -> None:
        self.setObjectName("secondary")

        self.__vlayout = QVBoxLayout()
        self.__vlayout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.setLayout(self.__vlayout)

        self.__init_header()
        self.__init_instance_widgets()

    def __init_header(self) -> None:
        glayout = QGridLayout()
        glayout.setContentsMargins(0, 0, 0, 0)
        glayout.setColumnStretch(0, 1)
        glayout.setColumnStretch(1, 3)
        self.__vlayout.addLayout(glayout)

        mod_manager_label = QLabel(self.tr("Mod Manager:"))
        glayout.addWidget(mod_manager_label, 1, 0)

        self.__mod_manager_dropdown = QComboBox()
        self.__mod_manager_dropdown.installEventFilter(self)
        self.__mod_manager_dropdown.setEditable(False)
        self.__mod_manager_dropdown.addItem(self.tr("Please select..."))
        self.__mod_manager_dropdown.addItems(
            [mod_manager.get_display_name() for mod_manager in MOD_MANAGERS]
        )
        for m, mod_manager in enumerate(MOD_MANAGERS, start=1):
            self.__mod_manager_dropdown.setItemIcon(
                m, QIcon(mod_manager.get_icon_name())
            )
        self.__mod_manager_dropdown.currentTextChanged.connect(
            self.__on_mod_manager_select
        )
        glayout.addWidget(self.__mod_manager_dropdown, 1, 1)

    def __init_instance_widgets(self) -> None:
        self.__instance_stack_layout = QStackedLayout()
        self.__instance_stack_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.__placeholder_widget = QWidget()
        self.__instance_stack_layout.addWidget(self.__placeholder_widget)
        self.__vlayout.addLayout(self.__instance_stack_layout)

        self.__mod_managers = {}
        mod_manager_ids: dict[str, type[ModManager]] = {
            mod_manager.get_id(): mod_manager for mod_manager in MOD_MANAGERS
        }

        for instance_widget_type in INSTANCE_WIDGETS:
            mod_manager: ModManager = mod_manager_ids[instance_widget_type.get_id()]()
            instance_widget: BaseSelectorWidget = instance_widget_type()

            instance_widget.changed.connect(self.changed.emit)
            instance_widget.valid.connect(self.__on_valid)

            self.__instance_stack_layout.addWidget(instance_widget)
            self.__mod_managers[mod_manager] = instance_widget

    def set_cur_game(self, game: Optional[Game]) -> None:
        """
        Sets the current game of the instance selector widget.

        Args:
            game (Optional[Game]): The game
        """

        self.__cur_game = game

        # Reset selected instance
        self.__mod_manager_dropdown.setCurrentIndex(0)
        self.__cur_mod_manager = None
        self.__cur_instance_data = None

    def __on_mod_manager_select(self, value: str) -> None:
        mod_manager_names: dict[str, ModManager] = {
            mod_manager.get_display_name(): mod_manager
            for mod_manager in self.__mod_managers.keys()
        }

        selected_mod_manager: Optional[ModManager] = mod_manager_names.get(value)

        self.__set_cur_mod_manager(selected_mod_manager)

    def __set_cur_mod_manager(self, mod_manager: Optional[ModManager]) -> None:
        if mod_manager is not None:
            game: Optional[Game] = self.__cur_game

            if game is None:
                raise ValueError("No game selected.")

            instance_widget: BaseSelectorWidget = self.__mod_managers[mod_manager]
            instance_widget.set_instances(mod_manager.get_instance_names(game))
            self.__instance_stack_layout.setCurrentWidget(instance_widget)
            self.__on_valid(instance_widget.validate())
        else:
            cur_widget: QWidget = self.__instance_stack_layout.currentWidget()
            if isinstance(cur_widget, BaseSelectorWidget):
                cur_widget.reset()
            self.__instance_stack_layout.setCurrentWidget(self.__placeholder_widget)
            self.__on_valid(False)

        self.__cur_mod_manager = mod_manager
        self.changed.emit()

    def __on_valid(self, valid: bool) -> None:
        if valid and self.__cur_mod_manager is not None and self.__cur_game is not None:
            instance_widget: BaseSelectorWidget = self.__mod_managers[
                self.__cur_mod_manager
            ]
            if instance_widget.validate():
                self.__cur_instance_data = instance_widget.get_instance(self.__cur_game)
            else:
                self.__cur_instance_data = None
        else:
            self.__cur_instance_data = None

        self.instance_valid.emit(self.__cur_instance_data is not None)

    def validate(self) -> bool:
        """
        Returns whether the currently selected instance data is valid.

        Returns:
            bool: whether the currently selected instance data is valid
        """

        if self.__cur_mod_manager is not None and self.__cur_game is not None:
            instance_widget: BaseSelectorWidget = self.__mod_managers[
                self.__cur_mod_manager
            ]
            return instance_widget.validate()

        return False

    def get_cur_instance_data(self) -> InstanceInfo:
        """
        Returns the currently selected instance data.

        Raises:
            ValueError: when no instance data is selected.

        Returns:
            InstanceInfo: The instance data.
        """

        if self.__cur_instance_data is None:
            raise ValueError("No instance data selected.")

        return self.__cur_instance_data

    def get_selected_mod_manager(self) -> Optional[ModManager]:
        """
        Returns the currently selected mod manager.

        Returns:
            Optional[ModManager]: The selected mod manager or None.
        """

        return self.__cur_mod_manager

    @override
    def eventFilter(self, source: QObject, event: QEvent) -> bool:
        if (
            event.type() == QEvent.Type.Wheel
            and (isinstance(source, QComboBox) or isinstance(source, QSpinBox))
            and isinstance(event, QWheelEvent)
        ):
            self.wheelEvent(event)
            return True

        return super().eventFilter(source, event)
