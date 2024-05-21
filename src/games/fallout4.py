"""
This file is part of Mod Manager Migrator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

from main import MainApp

from .game import GameInstance


class Fallout4Instance(GameInstance):
    """
    Class for Fallout 4 GameInstance.
    Inherited from GameInstance class.
    """

    icon_name = "Fallout4.ico"

    def __init__(self, app: MainApp):
        super().__init__(app)

        self.name = "Fallout 4"
        self.id = "Fallout4"
        self.inidir = self.app.doc_path / "My Games" / "Fallout4"
        self.inifiles = [
            self.inidir / "Fallout4.ini",
            self.inidir / "Fallout4Prefs.ini",
            self.inidir / "Fallout4Custom.ini",
        ]
        self.reg_paths = [
            "HKEY_LOCAL_MACHINE\\SOFTWARE\\WOW6432Node\\Bethesda Softworks\\Fallout4\\installed path",
            "HKEY_LOCAL_MACHINE\\SOFTWARE\\WOW6432Node\\GOG.com\\Games\\1998527297\\path",
        ]

    def __repr__(self):
        return "Fallout4Instance"
