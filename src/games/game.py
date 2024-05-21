"""
This file is part of Mod Manager Migrator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

import logging
import winreg
from pathlib import Path

import qtpy.QtCore as qtc
import qtpy.QtWidgets as qtw

from main import MainApp
from utilities import UiException


class GameInstance:
    """
    General class for game instances.
    """

    icon_name = ""

    def __init__(self, app: MainApp):
        self.app = app
        self.loc = app.loc
        self.name: str = ""
        self.id: str = ""
        self.installdir: Path = ""
        self.inidir: Path = ""
        self.inifiles: list[Path] = []
        self.reg_paths: list[str] = []

        # Initialize class specific logger
        self.log = logging.getLogger(self.__repr__())

    def __repr__(self):
        return "GameInstance"

    def get_install_dir(self):
        """
        Gets game's install directory and returns it.

        If steamid is given, get the install location from there.

        If this fails, it tries to get the install location from GOG if that id is given.
        """

        installdir = self.installdir

        # Only search for installdir if not already done
        if not installdir:
            # Try to get Skyrim path from Steam if installed
            for reg_path in self.reg_paths:
                try:
                    key, reg_path = reg_path.split("\\", 1)
                    reg_path, value_name = reg_path.rsplit("\\", 1)
                    key: int = getattr(winreg, key, winreg.HKEY_LOCAL_MACHINE)
                    with winreg.OpenKey(key, reg_path) as hkey:
                        installdir = Path(
                            winreg.QueryValueEx(hkey, value_name)[0]
                        )

                        if installdir.is_dir() and str(installdir) != ".":
                            self.installdir = installdir
                            return self.installdir

                except Exception as ex:
                    self.log.error(f"Failed to get install path from Registry Key {reg_path!r}: {ex}")

        if not self.installdir:
            dialog = qtw.QDialog()
            dialog.setModal(True)
            dialog.setWindowTitle(self.app.name)
            dialog.setWindowIcon(self.app.root.windowIcon())
            dialog.setStyleSheet(self.app.stylesheet)
            # dialog.setWindowFlag(qtc.Qt.WindowType.WindowCloseButtonHint, False)

            layout = qtw.QGridLayout()
            dialog.setLayout(layout)

            label = qtw.QLabel(self.loc.main.game_not_found)
            label.setAlignment(qtc.Qt.AlignmentFlag.AlignHCenter)
            layout.addWidget(label, 0, 0, 1, 2)

            lineedit = qtw.QLineEdit()
            layout.addWidget(lineedit, 1, 0)

            def on_edit(text: str):
                # Enable button if path is valid or empty
                if Path(text).is_dir() or (not text.strip()):
                    continue_button.setDisabled(False)
                # Disable it otherwise
                else:
                    continue_button.setDisabled(True)

            lineedit.textChanged.connect(on_edit)

            def browse_path():
                file_dialog = qtw.QFileDialog(dialog)
                file_dialog.setWindowTitle(self.loc.main.browse)
                file_dialog.setDirectory(lineedit.text())
                file_dialog.setFileMode(qtw.QFileDialog.FileMode.Directory)
                if file_dialog.exec():
                    folder = file_dialog.selectedFiles()[0]
                    folder = Path(folder)
                    lineedit.setText(str(folder))

            browse_button = qtw.QPushButton(self.loc.main.browse)
            browse_button.clicked.connect(browse_path)
            layout.addWidget(browse_button, 1, 1)

            continue_button = qtw.QPushButton(self.loc.main._continue)
            continue_button.setDisabled(True)
            continue_button.clicked.connect(dialog.accept)
            layout.addWidget(continue_button, 2, 1)

            if dialog.exec():
                installdir = Path(lineedit.text())
                if installdir.is_dir() and str(installdir).strip():
                    self.installdir = installdir
                else:
                    raise UiException("[invalid_path] Path is invalid!")
            else:
                return Path(" ")

        self.log.debug(f"Game install path: {self.installdir}")
        return self.installdir
