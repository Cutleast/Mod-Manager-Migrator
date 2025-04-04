"""
Copyright (c) Cutleast
"""

from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFileDialog,
    QGridLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QStackedLayout,
    QVBoxLayout,
    QWidget,
)

from app_context import AppContext
from core.game.exceptions import GameNotFoundError
from core.game.game import Game
from core.instance.instance import Instance
from core.migrator.file_blacklist import FileBlacklist
from core.mod_manager import MOD_MANAGERS
from core.mod_manager.instance_info import InstanceInfo
from core.mod_manager.mod_manager import ModManager
from ui.widgets.loading_dialog import LoadingDialog

from . import INSTANCE_WIDGETS
from .instance import InstanceWidget


class InstanceSelector(QWidget):
    """
    Widget for selecting the source instance.
    """

    instance_selected = Signal(Instance)
    """
    This signal is emitted when an instance is selected.
    """

    __games: dict[str, Game] = {
        game.display_name: game for game in Game.get_supported_games()
    }
    """
    Maps games to their names.
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

    __cur_mod_instance: Optional[Instance] = None
    """
    Currently selected mod instance.
    """

    __mod_managers: dict[ModManager, InstanceWidget]
    """
    Maps mod managers to their corresponding instance widgets.
    """

    __vlayout: QVBoxLayout
    __mod_manager_dropdown: QComboBox
    __instance_stack_layout: QStackedLayout
    __load_button: QPushButton
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
        title_label = QLabel(self.tr("Choose the source instance:"))
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

        game_label = QLabel(self.tr("Game:"))
        glayout.addWidget(game_label, 0, 0)

        self.__game_dropdown = QComboBox()
        self.__game_dropdown.setEditable(False)
        self.__game_dropdown.addItem(self.tr("Please select..."))
        self.__game_dropdown.addItems(list(self.__games.keys()))
        for g, game in enumerate(self.__games.values(), start=1):
            self.__game_dropdown.setItemIcon(g, QIcon(f":/icons/{game.short_name}.ico"))
        self.__game_dropdown.currentTextChanged.connect(self.__on_game_select)
        glayout.addWidget(self.__game_dropdown, 0, 1)

        mod_manager_label = QLabel(self.tr("Mod Manager:"))
        glayout.addWidget(mod_manager_label, 1, 0)

        self.__mod_manager_dropdown = QComboBox()
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
        self.__mod_manager_dropdown.setDisabled(True)
        glayout.addWidget(self.__mod_manager_dropdown, 1, 1)

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

            instance_widget.changed.connect(
                lambda: self.__load_button.setText(self.tr("Load selected instance..."))
            )
            instance_widget.valid.connect(
                lambda valid: self.__load_button.setEnabled(valid)
            )

            self.__instance_stack_layout.addWidget(instance_widget)
            self.__mod_managers[mod_manager] = instance_widget

    def __init_footer(self) -> None:
        self.__load_button = QPushButton(self.tr("Load selected instance..."))
        self.__load_button.setEnabled(False)
        self.__load_button.setObjectName("primary")
        self.__load_button.clicked.connect(self.load_instance)
        self.__vlayout.addWidget(self.__load_button)

        self.__vlayout.addStretch()

    def __on_game_select(self, value: str) -> None:
        selected_game: Optional[Game] = self.__games.get(value)

        if selected_game is not None:
            try:
                selected_game.installdir
            except GameNotFoundError:
                QMessageBox.warning(
                    AppContext.get_app().main_window,
                    self.tr("Could not find game directory!"),
                    self.tr(
                        "Unable to find game directory. Please select it manually."
                    ),
                    buttons=QMessageBox.StandardButton.Ok,
                )

                file_dialog = QFileDialog(
                    AppContext.get_app().main_window,
                    caption=self.tr("Select game directory"),
                    fileMode=QFileDialog.FileMode.Directory,
                )

                if file_dialog.exec() == QDialog.DialogCode.Accepted:
                    folder_path = Path(file_dialog.selectedFiles()[0])

                    if not folder_path.is_dir():
                        raise FileNotFoundError(folder_path)

                    selected_game.installdir = folder_path
                else:
                    self.__game_dropdown.setCurrentIndex(0)
                    return

        self.__set_cur_game(selected_game)

    def __set_cur_game(self, game: Optional[Game]) -> None:
        self.__mod_manager_dropdown.setEnabled(game is not None)
        self.__cur_game = game

    def __on_mod_manager_select(self, value: str) -> None:
        mod_manager_names: dict[str, ModManager] = {
            mod_manager.display_name: mod_manager
            for mod_manager in self.__mod_managers.keys()
        }

        selected_mod_manager: Optional[ModManager] = mod_manager_names.get(value)

        self.__set_cur_mod_manager(selected_mod_manager)

    def __set_cur_mod_manager(self, mod_manager: Optional[ModManager]) -> None:
        game: Optional[Game] = self.__cur_game

        if game is None:
            raise ValueError("No game selected.")

        if mod_manager is not None:
            instance_widget: InstanceWidget = self.__mod_managers[mod_manager]
            instance_widget.set_instances(mod_manager.get_instance_names(game))
            self.__instance_stack_layout.setCurrentWidget(instance_widget)
            self.__load_button.setEnabled(instance_widget.validate())
        else:
            self.__instance_stack_layout.setCurrentWidget(self.__placeholder_widget)
            self.__load_button.setDisabled(True)

        self.__cur_mod_manager = mod_manager
        self.__load_button.setText(self.tr("Load selected instance..."))

    def load_instance(self) -> Instance:
        """
        Loads and returns the mod instance from the current selection.

        Returns:
            Instance: The mod instance.
        """

        mod_manager: Optional[ModManager] = self.__cur_mod_manager
        if mod_manager is None:
            raise ValueError("No mod manager selected.")

        game: Optional[Game] = self.__cur_game
        if game is None:
            raise ValueError("No game selected.")

        instance_data = self.__mod_managers[mod_manager].get_instance(game)
        self.__cur_mod_instance = LoadingDialog.run_callable(
            lambda ldialog: mod_manager.load_instance(
                instance_data, FileBlacklist.get_files(), ldialog
            )
        )
        self.instance_selected.emit(self.__cur_mod_instance)

        self.__load_button.setText(self.tr("Instance loaded."))
        self.__load_button.setDisabled(True)

        self.__cur_instance_data = instance_data

        return self.__cur_mod_instance

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

    def get_cur_mod_instance(self) -> Optional[Instance]:
        """
        Returns the currently selected mod instance or None.

        Returns:
            Optional[Instance]: The mod instance or None.
        """

        return self.__cur_mod_instance

    def get_cur_game(self) -> Optional[Game]:
        """
        Returns the currently selected game or None.

        Returns:
            Optional[Game]: The game or None.
        """

        return self.__cur_game
