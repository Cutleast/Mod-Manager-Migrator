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
    QPushButton,
    QSpinBox,
    QStackedLayout,
    QVBoxLayout,
    QWidget,
)

from app_context import AppContext
from core.game.game import Game
from core.mod_manager import MOD_MANAGERS
from core.mod_manager.instance_info import InstanceInfo
from core.mod_manager.mod_manager import ModManager

from . import INSTANCE_WIDGETS
from .instance import InstanceWidget


class InstanceCreator(QWidget):
    """
    Widget for creating and customizing the destination instance.
    """

    instance_valid = Signal(bool)
    """
    This signal is emitted when the instance is valid.
    """

    __sel_mod_manager: Optional[ModManager] = None
    """
    Selected destination mod manager.
    """

    __mod_managers: dict[ModManager, InstanceWidget]
    """
    Maps mod managers to their corresponding instance widgets.
    """

    __vlayout: QVBoxLayout
    __mod_manager_dropdown: QComboBox
    __instance_stack_layout: QStackedLayout
    __migrate_button: QPushButton
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
        self.__init_footer()

    def __init_header(self) -> None:
        # Title label
        title_label = QLabel(self.tr("Configure the destination instance:"))
        title_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        title_label.setObjectName("h3")
        self.__vlayout.addWidget(title_label, 0, Qt.AlignmentFlag.AlignHCenter)
        self.__vlayout.addSpacing(25)

        # Mod Manager selection
        glayout = QGridLayout()
        glayout.setContentsMargins(0, 0, 0, 0)
        glayout.setColumnStretch(0, 1)
        glayout.setColumnStretch(1, 3)
        self.__vlayout.addLayout(glayout)

        mod_manager_label = QLabel(self.tr("Mod Manager:"))
        glayout.addWidget(mod_manager_label, 0, 0)

        self.__mod_manager_dropdown = QComboBox()
        self.__mod_manager_dropdown.installEventFilter(self)
        self.__mod_manager_dropdown.setEditable(False)
        self.__mod_manager_dropdown.addItem(self.tr("Please select..."))
        self.__mod_manager_dropdown.addItems(
            [mod_manager.display_name for mod_manager in MOD_MANAGERS]
        )
        for m, mod_manager in enumerate(MOD_MANAGERS, start=1):
            self.__mod_manager_dropdown.setItemIcon(m, QIcon(mod_manager.icon_name))

        self.__mod_manager_dropdown.currentTextChanged.connect(
            self.__on_mod_manager_select
        )
        glayout.addWidget(self.__mod_manager_dropdown, 0, 1)

    def __init_instance_widgets(self) -> None:
        self.__instance_stack_layout = QStackedLayout()
        self.__instance_stack_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.__placeholder_widget = QWidget()
        self.__instance_stack_layout.addWidget(self.__placeholder_widget)
        self.__vlayout.addLayout(self.__instance_stack_layout)

        self.__mod_managers = {}
        mod_manager_ids: dict[str, type[ModManager]] = {
            mod_manager.id: mod_manager for mod_manager in MOD_MANAGERS
        }

        for instance_widget_type in INSTANCE_WIDGETS:
            mod_manager: ModManager = mod_manager_ids[instance_widget_type.id]()

            instance_widget: InstanceWidget = instance_widget_type()
            instance_widget.valid.connect(
                lambda valid: self.__migrate_button.setEnabled(valid)
            )

            self.__instance_stack_layout.addWidget(instance_widget)
            self.__mod_managers[mod_manager] = instance_widget

    def __init_footer(self) -> None:
        self.__migrate_button = QPushButton(self.tr("Migrate..."))
        self.__migrate_button.setEnabled(False)
        self.__migrate_button.setObjectName("primary")
        self.__migrate_button.clicked.connect(AppContext.get_app().migrate)
        self.__vlayout.addWidget(self.__migrate_button)

        self.__vlayout.addStretch()

    def __on_mod_manager_select(self, value: str) -> None:
        mod_manager_names: dict[str, ModManager] = {
            mod_manager.display_name: mod_manager
            for mod_manager in self.__mod_managers.keys()
        }

        selected_mod_manager: Optional[ModManager] = mod_manager_names.get(value)

        self.__set_cur_mod_manager(selected_mod_manager)

    def __set_cur_mod_manager(self, mod_manager: Optional[ModManager]) -> None:
        if mod_manager is not None:
            instance_widget: InstanceWidget = self.__mod_managers[mod_manager]
            self.__instance_stack_layout.setCurrentWidget(instance_widget)
            self.__migrate_button.setEnabled(instance_widget.validate())
        else:
            self.__instance_stack_layout.setCurrentWidget(self.__placeholder_widget)
            self.__migrate_button.setDisabled(True)

        self.__sel_mod_manager = mod_manager

    def get_selected_mod_manager(self) -> Optional[ModManager]:
        """
        Returns the currently selected mod manager.

        Returns:
            Optional[ModManager]: The selected mod manager.
        """

        return self.__sel_mod_manager

    def get_instance_data(self, game: Game) -> InstanceInfo:
        """
        Returns the customized destination instance data.

        Args:
            game (Game): The selected game.

        Raises:
            ValueError:
                when no mod manager is selected or the customized instance is invalid.

        Returns:
            InstanceData: The customized destination instance data.
        """

        mod_manager: Optional[ModManager] = self.get_selected_mod_manager()

        if mod_manager is None:
            raise ValueError("No mod manager selected!")

        instance_widget: InstanceWidget = self.__mod_managers[mod_manager]

        if not instance_widget.validate():
            raise ValueError("Customized instance data is invalid!")

        return instance_widget.get_instance(game)

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
