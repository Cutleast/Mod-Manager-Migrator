"""
This file is part of Mod Manager Migrator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

import logging
from pathlib import Path

import qtpy.QtCore as qtc
import qtpy.QtGui as qtg
import qtpy.QtWidgets as qtw

import utilities as utils
from widgets import LoadingDialog
from main import MainApp


class ModInstance:
    """
    General class for mod manager instances.
    """

    icon_name = ""

    def __init__(self, app: MainApp):
        self.app = app

        # Initialize class specific logger
        self.log = logging.getLogger(self.__repr__())

        # Name of current instance/profile
        self.name: str = None

        # list of installed mods
        self.mods: list[utils.Mod] = []

        # list of mods that must be copied
        # directly to the game folder
        self.root_mods: list[utils.Mod] = []

        # file: [origin mod, origin mod, etc...]
        self.modfiles: dict[Path, list[utils.Mod]] = {}

        # size in bytes as integer
        self._size: int = 0

        # list of mods sorted in loadorder
        self._loadorder: list[utils.Mod] = []

        # loadorder.txt, plugins.txt, game inis, etc.
        self.additional_files: list[Path] = []

        # path to mod folder
        self.mods_path: Path = ""

        # list of existing instances
        self.instances: list[str] = []

        # contains additional paths like download folder
        self.paths: dict[str, Path] = {}

        # instance data like name, paths
        self.instance_data = {}

    def __repr__(self):
        return "ModInstance"

    def setup_instance(self):
        """
        Sets up instance files and configures instance.

        Takes data from self.instance_data.
        """

        return

    def load_instances(self):
        """
        Gets list of instances and returns it.
        """

        return self.instances

    def load_instance(self, name: str, ldialog: LoadingDialog = None):
        """
        Loads instance with name <name>.
        """

        self.name = name

    def copy_mods(self, ldialog: LoadingDialog = None):
        """
        Copies mods from source instance to destination instance.

        Gets called by destination instance.
        """

        return

    def copy_files(self, ldialog: LoadingDialog = None):
        """
        Copies additional files from source instance
        to destination instance.

        Gets called by destination instance.
        """

        return

    def get_file_conflicts(self):
        """
        Gets separate files conflicts and converts them.
        """

        return

    def set_file_conflicts(self):
        """
        Converts source's file conflicts to this mod manager's format.
        """

        return

    def show_src_widget(self):
        """
        Shows widget with instance details and mods
        at source position.
        """

        self._show_widget("src")

    def show_dst_widget(self):
        """
        Shows widget with instance details and mods
        at source position.
        """

        self._show_widget("dst")

    def _show_widget(self, pos: str):
        """
        Shows widget. Internal use only!

        Use 'show_src_widget' or 'show_dst_widget' instead!
        """

        # Create widget with instance details
        self.widget = qtw.QWidget()
        self.widget.setObjectName("panel")

        # Create layout
        layout = qtw.QGridLayout()
        layout.setAlignment(qtc.Qt.AlignmentFlag.AlignTop)
        layout.setColumnStretch(2, 1)
        self.widget.setLayout(layout)

        # Add label with mod manager icon
        label = qtw.QLabel(f"{self.app.lang['mod_manager']}:")
        layout.addWidget(label, 0, 0)
        icon = qtg.QPixmap(str(self.app.ico_path / self.icon_name))
        label = qtw.QLabel()
        label.setAlignment(qtc.Qt.AlignmentFlag.AlignCenter)
        size = qtc.QSize(375, 125)
        label.resize(size)
        label.setFixedSize(size)
        label.setScaledContents(True)
        # icon = icon.scaled(size, qtc.Qt.AspectRatioMode.KeepAspectRatio)
        label.setPixmap(icon)
        layout.addWidget(label, 0, 1)

        # Add label with instance name
        label = qtw.QLabel(f"{self.app.lang['instance_name']}:")
        layout.addWidget(label, 1, 0)
        label = qtw.QLabel(self.name)
        layout.addWidget(label, 1, 1)

        # Add label with game name
        label = qtw.QLabel(f"{self.app.lang['game']}:")
        layout.addWidget(label, 2, 0)
        label = qtw.QLabel(self.app.game_instance.name)
        layout.addWidget(label, 2, 1)

        # Add label with mods path
        label = qtw.QLabel(f"{self.app.lang['mods_path']}:")
        layout.addWidget(label, 3, 0)
        path = str(self.mods_path)
        path = utils.wrap_string(path, 50)
        label = qtw.QLabel(path)
        label.setTextInteractionFlags(qtc.Qt.TextInteractionFlag.TextSelectableByMouse)
        label.setCursor(qtc.Qt.CursorShape.IBeamCursor)
        label.setWordWrap(True)
        layout.addWidget(label, 3, 1)

        # Add label with instance size
        if pos == "src":
            label = qtw.QLabel(f"{self.app.lang['size']}:")
            layout.addWidget(label, 4, 0)
            label = qtw.QLabel(utils.scale_value(self.size))
            layout.addWidget(label, 4, 1)
        else:
            label = qtw.QLabel(f"{self.app.lang['mode']}:")
            layout.addWidget(label, 4, 0)
            label = qtw.QLabel(self.app.lang[f"{self.app.mode}_mode"])
            layout.addWidget(label, 4, 1)

        # Add label with mods count
        label = qtw.QLabel(f"{self.app.lang['number_of_mods']}:")
        layout.addWidget(label, 5, 0)
        self.mods_count_label = qtw.QLabel(str(len(self.mods)))
        layout.addWidget(self.mods_count_label, 5, 1)

        # Add spacer
        spacer = qtw.QWidget()
        spacer.setFixedHeight(20)
        layout.addWidget(spacer, 6, 0)

        # Add listbox for source mods
        if pos == "src":
            label = qtw.QLabel(self.app.lang["mods_to_migrate"])
        else:
            label = qtw.QLabel(self.app.lang["mods_to_enable"])
        layout.addWidget(label, 7, 0)
        self.mods_box = qtw.QListWidget()
        self.mods_box.setSelectionMode(qtw.QListWidget.SelectionMode.MultiSelection)
        self.mods_box.setHorizontalScrollBarPolicy(
            qtc.Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
        self.mods_box.itemDoubleClicked.connect(lambda item: item.onClick())
        self.mods_box.setContextMenuPolicy(qtc.Qt.ContextMenuPolicy.CustomContextMenu)
        self.mods_box.customContextMenuRequested.connect(
            lambda pos: self._contextmenu(self.mods_box.mapToGlobal(pos))
        )
        layout.addWidget(self.mods_box, 8, 0, 1, 3)

        # Add mods to listbox
        self._update_listbox(pos)

        # Show widget as source
        if pos == "src":
            self.mods_box.itemChanged.connect(
                lambda item: self.app.migrate_mods_change_sign.emit()
            )
            if self.app.src_widget is not None:
                self.app.src_widget.destroy()
            self.app.mainlayout.addWidget(self.widget, 1, 0)
            self.app.src_widget = self.widget

        # Or show widget as destination
        elif pos == "dst":
            try:
                self.app.migrate_mods_change_sign.disconnect()
            except:
                pass
            self.app.migrate_mods_change_sign.connect(lambda: self._update_listbox(pos))
            if self.app.dst_widget is not None:
                self.app.dst_widget.destroy()
            self.app.mainlayout.addWidget(self.widget, 1, 2)
            self.app.dst_widget = self.widget

    def _contextmenu(self, pos: qtc.QPoint):
        """
        Shows context menu. Internal use only!
        """

        select_action = qtg.QAction(self.app.lang["enable_selected"])
        select_action.triggered.connect(self._enable_selected)
        unselect_action = qtg.QAction(self.app.lang["disable_selected"])
        unselect_action.triggered.connect(self._disable_selected)
        unsel_all_action = qtg.QAction(self.app.lang["unselect_all"])
        unsel_all_action.triggered.connect(self._unselect_all)
        context_menu = qtw.QMenu()
        context_menu.setWindowFlags(
            qtc.Qt.WindowType.FramelessWindowHint
            | qtc.Qt.WindowType.Popup
            | qtc.Qt.WindowType.NoDropShadowWindowHint
        )
        context_menu.setAttribute(
            qtc.Qt.WidgetAttribute.WA_TranslucentBackground, on=True
        )
        context_menu.setStyleSheet(self.app.stylesheet)
        context_menu.addAction(select_action)
        context_menu.addAction(unselect_action)
        context_menu.addAction(unsel_all_action)

        # Show context menu
        context_menu.exec(pos)

    def _enable_selected(self):
        """
        Enables selected mods. Internal use only!
        """

        for item in self.mods_box.selectedItems():
            if item.checkState() != qtc.Qt.CheckState.Checked:
                self.mods_box.itemDoubleClicked.emit(item)

    def _disable_selected(self):
        """
        Disables selected mods. Internal use only!
        """

        for item in self.mods_box.selectedItems():
            if item.checkState() != qtc.Qt.CheckState.Unchecked:
                self.mods_box.itemDoubleClicked.emit(item)

    def _unselect_all(self):
        """
        Unselects all mods. Internal use only!
        """

        for item in self.mods_box.selectedItems():
            item.setSelected(False)

    def _update_listbox(self, pos: str):
        """
        Updates listbox. Internal use only!
        """

        if self.widget is not None:
            try:
                self.mods_box.itemChanged.disconnect()
            except:
                pass
            self.mods_box.clear()
            for mod in self.loadorder:
                if not mod.selected and pos == "dst":
                    continue
                item = utils.mod_item.ModItem(mod, pos, mod.name, self.mods_box)
                item.setFlags(item.flags() | qtc.Qt.ItemFlag.ItemIsUserCheckable)
                if pos == "dst":
                    if mod.enabled:
                        item.setCheckState(qtc.Qt.CheckState.Checked)
                    else:
                        item.setCheckState(qtc.Qt.CheckState.Unchecked)
                else:
                    mod.selected = True
                    item.setCheckState(qtc.Qt.CheckState.Checked)
                self.mods_box.addItem(item)

            self.mods_count_label.setText(str(self.mods_box.count()))

            self.mods_box.itemChanged.connect(lambda item: item.onClick())

    @property
    def loadorder(self):
        """
        Gets sorted loadorder.
        """

        if not self._loadorder:
            self._loadorder = self.mods.copy()
            self._loadorder.sort(key=lambda mod: mod.name)
        return self._loadorder

    @loadorder.setter
    def loadorder(self, loadorder: list, ldialog: LoadingDialog = None):
        """
        Sets loadorder.
        """

        self._loadorder = loadorder

    @property
    def size(self):
        """
        Calculates total size of mods. Returns it in bytes as integer.
        """

        self._size = sum([mod.size for mod in self.loadorder])

        return self._size
