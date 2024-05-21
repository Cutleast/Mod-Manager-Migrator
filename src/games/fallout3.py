"""
This file is part of Mod Manager Migrator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

from main import MainApp

from .game import GameInstance


class Fallout3Instance(GameInstance):
    """
    Class for Fallout3 GameInstance.
    Inherited from GameInstance class.
    """

    icon_name = "Fallout3.ico"

    def __init__(self, app: MainApp):
        super().__init__(app)

        self.name = "Fallout 3"
        self.id = "Fallout3"
        self.inidir = self.app.doc_path / "My Games" / "Fallout3"
        self.inifiles = [
            self.inidir / "Fallout.ini",
            self.inidir / "FalloutPrefs.ini",
        ]
        self.reg_paths = [
            "HKEY_LOCAL_MACHINE\\SOFTWARE\\WOW6432Node\\Bethesda Softworks\\Fallout3\\installed path",
            "HKEY_LOCAL_MACHINE\\SOFTWARE\\WOW6432Node\\GOG.com\\Games\\1248282609\\path",
        ]

    def __repr__(self):
        return "Fallout3Instance"
