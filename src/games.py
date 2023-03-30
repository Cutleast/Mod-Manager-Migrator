"""
Part of MMM. Contains game classes.

Falls under license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

import os
import winreg
from pathlib import Path
from typing import List

from main import MainApp, qtw, qtc


# Create class for Game instance #####################################
class GameInstance:
    """
    General class for game instances.
    """

    def __init__(self, app: MainApp):
        self.app = app
        self.name: str = ""
        self.installdir: Path = ""
        self.inidir: Path = ""
        self.inifiles: List[Path] = []
        self.steamid: int = 0
        self.gogid: int = 0

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
                        if installdir.is_dir():
                            self.installdir = installdir
                            return self.installdir
                except Exception as ex:
                    self.app.log.error(
                        f"Failed to get install path from Steam: {ex}"
                    )

            # Try to get Skyrim path from GOG if installed
            if self.gogid:
                try:
                    reg_path = f"\
SOFTWARE\\WOW6432Node\\GOG.com\\Games\\{self.gogid}"
                    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path) as hkey:
                        installdir = Path(
                            winreg.QueryValueEx(hkey, "path")[0]
                        )
                        if installdir.is_dir():
                            self.installdir = installdir
                            return self.installdir
                except Exception as ex:
                    self.app.log.error(f"Failed to get install path from Steam: {ex}")

        if not installdir:
            dialog = qtw.QDialog()
            dialog.setModal(True)
            dialog.setWindowTitle(self.app.name)
            dialog.setWindowIcon(self.app.root.windowIcon())
            dialog.setStyleSheet(self.app.stylesheet)
            dialog.setWindowFlag(qtc.Qt.WindowType.WindowCloseButtonHint, False)

            layout = qtw.QGridLayout()
            dialog.setLayout(layout)

            label = qtw.QLabel(self.app.lang['game_not_found'])
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
                file_dialog.setWindowTitle(self.app.lang['browse'])
                file_dialog.setDirectory(lineedit.text())
                file_dialog.setFileMode(qtw.QFileDialog.FileMode.Directory)
                if file_dialog.exec():
                    folder = file_dialog.selectedFiles()[0]
                    folder = Path(folder)
                    lineedit.setText(folder)

            browse_button = qtw.QPushButton(self.app.lang['browse'])
            browse_button.clicked.connect(browse_path)
            layout.addWidget(browse_button, 1, 1)

            continue_button = qtw.QPushButton(self.app.lang['continue'])
            continue_button.setDisabled(True)
            continue_button.clicked.connect(dialog.accept)
            layout.addWidget(continue_button, 2, 1)

            dialog.exec()

            installdir = Path(lineedit.text())
            if installdir.is_dir():
                self.installdir = installdir
            else:
                raise ValueError("No path specified!")

        return self.installdir


# Create class for SkyrimSE instance #################################
class SkyrimSEInstance(GameInstance):
    """
    Class for SkyrimSE GameInstance. Inherited from GameInstance class.
    """

    def __init__(self, app: MainApp):
        super().__init__(app)

        self.name = "Skyrim Special Edition"
        self.inidir = Path(os.path.join(
                self.app.doc_path,
                'My Games',
                'Skyrim Special Edition'
            )
        )
        self.inifiles = ['Skyrim.ini', 'SkyrimPrefs.ini', 'SkyrimCustom.ini']
        self.steamid = 489830
        self.gogid = 1711230643

    def __repr__(self):
        return "SkyrimSEInstance"


# Create class for Skyrim ("Oldrim") instance ########################
class SkyrimInstance(GameInstance):
    """
    Class for Skyrim ("Oldrim") GameInstance. Inherited from GameInstance class.
    """

    def __init__(self, app: MainApp):
        super().__init__(app)

        self.name = "Skyrim"
        self.inidir = os.path.join(self.app.doc_path, 'My Games', 'Skyrim')
        self.inifiles = ['Skyrim.ini', 'SkyrimPrefs.ini', 'SkyrimCustom.ini']
        self.steamid = 72850

    def __repr__(self):
        return "SkyrimInstance"


# Create class for Fallout4 instance #################################
class Fallout4Instance(GameInstance):
    """
    Class for Fallout 4 GameInstance. Inherited from GameInstance class.
    """

    def __init__(self, app: MainApp):
        super().__init__(app)

        self.name = "Fallout 4"
        self.inidir = os.path.join(self.app.doc_path, 'My Games', 'Fallout 4')
        self.steamid = 377160

    def __repr__(self):
        return "Fallout4Instance"


# Create class for Enderal instance ##################################
class EnderalInstance(GameInstance):
    """
    Class for Enderal GameInstance. Inherited from GameInstance class.
    """

    def __init__(self, app: MainApp):
        super().__init__(app)

        self.name = "Enderal"
        self.inidir = os.path.join(self.app.doc_path, 'My Games', 'Enderal')
        self.steamid = 933480

    def __repr__(self):
        return "EnderalInstance"


# Create class for EnderalSE instance ##################################
class EnderalSEInstance(GameInstance):
    """
    Class for EnderalSE GameInstance. Inherited from GameInstance class.
    """

    def __init__(self, app: MainApp):
        super().__init__(app)

        self.name = "Enderal Special Edition"
        self.inidir = os.path.join(self.app.doc_path, 'My Games', 'Enderal Special Edition')
        self.steamid = 976620

    def __repr__(self):
        return "EnderalSEInstance"
