"""
This file is part of Mod Manager Migrator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

from main import MainApp

from .game import GameInstance


class OblivionInstance(GameInstance):
    """
    Class for FalloutNV GameInstance.
    Inherited from GameInstance class.
    """

    icon_name = "Oblivion.ico"

    def __init__(self, app: MainApp):
        super().__init__(app)

        self.name = "Oblivion"
        self.id = "Oblivion"
        self.inidir = self.app.doc_path / "My Games" / self.name
        self.inifiles = [
            self.inidir / "Oblivion.ini",
            self.inidir / "OblivionPrefs.ini",
            self.inidir / "BlendSettings.ini",
        ]
        self.reg_paths = [
            "HKEY_LOCAL_MACHINE\\SOFTWARE\\WOW6432Node\\Bethesda Softworks\\Oblivion\\installed path"
        ]

    def __repr__(self):
        return "OblivionInstance"
