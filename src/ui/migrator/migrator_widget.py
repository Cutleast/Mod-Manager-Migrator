"""
Copyright (c) Cutleast
"""

from pathlib import Path
from typing import Optional, override

import qtawesome as qta
from PySide6.QtCore import QEvent, QObject, Qt, Signal
from PySide6.QtGui import QIcon, QWheelEvent
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTabBar,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from core.config.app_config import AppConfig
from core.game.exceptions import GameNotFoundError
from core.game.game import Game
from core.instance.instance import Instance
from core.migrator.file_blacklist import FileBlacklist
from core.mod_manager.instance_info import InstanceInfo
from core.mod_manager.mod_manager import ModManager
from ui.widgets.loading_dialog import LoadingDialog
from ui.widgets.smooth_scroll_area import SmoothScrollArea

from .instance_creator.instance_creator_widget import InstanceCreatorWidget
from .instance_selector.instance_selector_widget import InstanceSelectorWidget


class MigratorWidget(SmoothScrollArea):
    """
    Widget for configuring and starting the migration process.
    """

    src_selected = Signal(Instance)
    """This signal gets emitted when the source instance is selected."""

    migration_started = Signal()
    """This signal gets emitted when the user clicks on the migrate button."""

    app_config: AppConfig

    __games: dict[str, Game]
    """Maps games to their names."""

    __game_folders: dict[Game, Path] = {}
    """Maps games to their game folders."""

    __cur_game: Optional[Game] = None
    """Currently selected game."""

    __cur_instance: Optional[Instance] = None
    """Currently loaded source instance."""

    __vlayout: QVBoxLayout
    __game_dropdown: QComboBox

    __src_selector: InstanceSelectorWidget
    __load_src_button: QPushButton

    __dst_instance_tab: QTabWidget
    __dst_selector: InstanceSelectorWidget
    __dst_creator: InstanceCreatorWidget
    __migrate_button: QPushButton

    def __init__(self, app_config: AppConfig) -> None:
        super().__init__()

        self.app_config = app_config
        self.__games = {game.display_name: game for game in Game.get_supported_games()}

        self.__init_ui()

        self.__src_selector.instance_valid.connect(self.__load_src_button.setEnabled)
        self.__src_selector.changed.connect(
            lambda: self.__load_src_button.setText(self.tr("Load selected instance..."))
        )
        self.__migrate_button.clicked.connect(self.migration_started.emit)
        self.__dst_creator.instance_valid.connect(self.__migrate_button.setEnabled)
        self.__dst_selector.instance_valid.connect(self.__migrate_button.setEnabled)
        self.__dst_instance_tab.currentChanged.connect(self.__on_dst_tab_change)

    def __init_ui(self) -> None:
        scroll_widget = QWidget()
        scroll_widget.setObjectName("transparent")
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

        self.__init_dst_instance_tab()
        self.__init_footer()

    def __init_game_dropdown(self) -> None:
        hlayout = QHBoxLayout()
        hlayout.addSpacing(9)
        self.__vlayout.addLayout(hlayout)

        game_label = QLabel(self.tr("Game:"))
        hlayout.addWidget(game_label)

        hlayout.addStretch()

        self.__game_dropdown = QComboBox()
        self.__game_dropdown.installEventFilter(self)
        self.__game_dropdown.setEditable(False)
        self.__game_dropdown.addItem(self.tr("Please select..."))
        self.__game_dropdown.addItems(list(self.__games.keys()))
        for g, game in enumerate(self.__games.values(), start=1):
            self.__game_dropdown.setItemIcon(g, QIcon(f":/icons/{game.short_name}.ico"))
        self.__game_dropdown.currentTextChanged.connect(self.__on_game_select)
        hlayout.addWidget(self.__game_dropdown)
        hlayout.addSpacing(9)

    def __init_src_selector(self) -> None:
        title_label = QLabel(self.tr("Choose the source instance:"))
        title_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        title_label.setObjectName("h3")
        self.__vlayout.addWidget(title_label, 0, Qt.AlignmentFlag.AlignHCenter)
        self.__vlayout.addSpacing(15)

        self.__init_game_dropdown()

        self.__src_selector = InstanceSelectorWidget()
        self.__src_selector.setDisabled(True)
        self.__vlayout.addWidget(self.__src_selector)

        self.__load_src_button = QPushButton(self.tr("Load selected instance..."))
        self.__load_src_button.setEnabled(False)
        self.__load_src_button.setObjectName("primary")
        self.__load_src_button.clicked.connect(self.__load_src_instance)
        self.__vlayout.addWidget(self.__load_src_button)

    def __init_dst_instance_tab(self) -> None:
        title_label = QLabel(self.tr("Configure the destination instance:"))
        title_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        title_label.setObjectName("h3")
        self.__vlayout.addWidget(title_label, 0, Qt.AlignmentFlag.AlignHCenter)
        self.__vlayout.addSpacing(15)

        self.__dst_instance_tab = QTabWidget()
        self.__dst_instance_tab.tabBar().setExpanding(True)
        self.__dst_instance_tab.setObjectName("centered_tab")
        self.__dst_instance_tab.setDisabled(True)
        self.__dst_instance_tab.tabBar().installEventFilter(self)
        self.__vlayout.addWidget(self.__dst_instance_tab)

        self.__dst_creator = InstanceCreatorWidget()
        self.__dst_instance_tab.addTab(
            self.__dst_creator, self.tr("Create new instance")
        )

        self.__dst_selector = InstanceSelectorWidget()
        self.__dst_instance_tab.addTab(
            self.__dst_selector,
            self.tr("Select existing instance") + " " + self.tr("(Experimental)"),
        )

    def __on_dst_tab_change(self, index: int) -> None:
        if index == 0:
            self.__migrate_button.setEnabled(self.__dst_creator.validate())
        else:
            self.__migrate_button.setEnabled(self.__dst_selector.validate())

    def __init_footer(self) -> None:
        self.__migrate_button = QPushButton(self.tr("Migrate..."))
        self.__migrate_button.setEnabled(False)
        self.__migrate_button.setObjectName("primary")
        self.__vlayout.addWidget(self.__migrate_button)

    def __on_game_select(self, value: str) -> None:
        self.__cur_game = self.__games.get(value)
        self.__src_selector.set_cur_game(self.__cur_game)
        self.__dst_selector.set_cur_game(self.__cur_game)
        self.__src_selector.setEnabled(self.__cur_game is not None)

        self.__cur_instance = None

    def __load_src_instance(self) -> None:
        mod_manager: Optional[ModManager] = (
            self.__src_selector.get_selected_mod_manager()
        )
        if mod_manager is None:
            raise ValueError("No mod manager selected.")

        game: Optional[Game] = self.__cur_game
        if game is None:
            raise ValueError("No game selected.")

        instance_data: InstanceInfo = self.__src_selector.get_cur_instance_data()
        mod_instance: Instance
        try:
            mod_instance = LoadingDialog.run_callable(
                lambda ldialog: mod_manager.load_instance(
                    instance_data=instance_data,
                    modname_limit=self.app_config.modname_limit,
                    file_blacklist=FileBlacklist.get_files(),
                    game_folder=self.__game_folders.get(game),
                    ldialog=ldialog,
                )
            )
        except GameNotFoundError:
            QMessageBox.warning(
                QApplication.activeModalWidget(),  # type: ignore
                self.tr("Could not find game directory!"),
                self.tr("Unable to find game directory. Please select it manually."),
                buttons=QMessageBox.StandardButton.Ok,
            )

            file_dialog = QFileDialog(
                QApplication.activeModalWidget(),
                caption=self.tr("Select game directory"),
                fileMode=QFileDialog.FileMode.Directory,
            )

            if file_dialog.exec() == QDialog.DialogCode.Accepted:
                folder_path = Path(file_dialog.selectedFiles()[0])

                if not folder_path.is_dir():
                    raise FileNotFoundError(folder_path)

                self.__game_folders[game] = folder_path
            else:
                self.__game_dropdown.setCurrentIndex(0)
        else:
            self.__load_src_button.setText(self.tr("Instance loaded."))
            self.__load_src_button.setDisabled(True)

            self.__cur_instance = mod_instance
            self.src_selected.emit(self.__cur_instance)

        self.__dst_instance_tab.setEnabled(self.get_src_instance() is not None)

    def get_selected_game(self) -> Optional[Game]:
        """
        Returns the currently selected game.

        Returns:
            Optional[Game]: The game
        """

        return self.__cur_game

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

        return self.__cur_instance

    def get_dst_mod_manager(self) -> Optional[ModManager]:
        """
        Returns the mod manager of the selected or configured destination instance.

        Returns:
            Optional[ModManager]: The mod manager
        """

        if self.__dst_instance_tab.currentWidget() is self.__dst_creator:
            return self.__dst_creator.get_selected_mod_manager()
        else:
            return self.__dst_selector.get_selected_mod_manager()

    def get_dst_instance_info(self, game: Game) -> InstanceInfo:
        """
        Returns the instance data for the selected or configured destination instance.

        Args:
            game (Game): The selected game

        Raises:
            ValueError: when the selected or configured destination instance is invalid

        Returns:
            InstanceInfo: The instance data
        """

        if self.__dst_instance_tab.currentWidget() is self.__dst_creator:
            return self.__dst_creator.get_instance_data(game)
        else:
            return self.__dst_selector.get_cur_instance_data()

    @override
    def eventFilter(self, source: QObject, event: QEvent) -> bool:
        if (
            event.type() == QEvent.Type.Wheel
            and isinstance(source, (QComboBox, QSpinBox, QTabBar))
            and isinstance(event, QWheelEvent)
        ):
            self.wheelEvent(event)
            return True

        return super().eventFilter(source, event)
