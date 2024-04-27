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
        self.name: str = ""
        self.id: str = ""
        self.installdir: Path = ""
        self.inidir: Path = ""
        self.inifiles: list[Path] = []
        self.steamid: int = 0
        self.gogid: int = 0

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
            if self.steamid:
                try:
                    reg_path = f"\
SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\Steam App {self.steamid}"
                    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path) as hkey:
                        installdir = Path(
                            winreg.QueryValueEx(hkey, "installLocation")[0]
                        )

                        if installdir.is_dir() and str(installdir) != ".":
                            self.installdir = installdir
                            # return self.installdir
                except Exception as ex:
                    self.log.error(f"Failed to get install path from Steam: {ex}")

            # Try to get Skyrim path from GOG if installed
            if self.gogid and (not self.installdir):
                try:
                    reg_path = f"\
SOFTWARE\\WOW6432Node\\GOG.com\\Games\\{self.gogid}"
                    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path) as hkey:
                        installdir = Path(winreg.QueryValueEx(hkey, "path")[0])

                    if installdir.is_dir() and str(installdir) != ".":
                        self.installdir = installdir
                        # return self.installdir
                except Exception as ex:
                    self.log.error(f"Failed to get install path from GOG: {ex}")

        if not self.installdir:
            dialog = qtw.QDialog()
            dialog.setModal(True)
            dialog.setWindowTitle(self.app.name)
            dialog.setWindowIcon(self.app.root.windowIcon())
            dialog.setStyleSheet(self.app.stylesheet)
            # dialog.setWindowFlag(qtc.Qt.WindowType.WindowCloseButtonHint, False)

            layout = qtw.QGridLayout()
            dialog.setLayout(layout)

            label = qtw.QLabel(self.app.lang["game_not_found"])
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
                file_dialog.setWindowTitle(self.app.lang["browse"])
                file_dialog.setDirectory(lineedit.text())
                file_dialog.setFileMode(qtw.QFileDialog.FileMode.Directory)
                if file_dialog.exec():
                    folder = file_dialog.selectedFiles()[0]
                    folder = Path(folder)
                    lineedit.setText(str(folder))

            browse_button = qtw.QPushButton(self.app.lang["browse"])
            browse_button.clicked.connect(browse_path)
            layout.addWidget(browse_button, 1, 1)

            continue_button = qtw.QPushButton(self.app.lang["continue"])
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
