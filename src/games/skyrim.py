"""
This file is part of Mod Manager Migrator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

from main import MainApp

from .game import GameInstance


class SkyrimInstance(GameInstance):
    """
    Class for Skyrim ("Oldrim") GameInstance.
    Inherited from GameInstance class.
    """

    icon_name = "Skyrim.ico"

    def __init__(self, app: MainApp):
        super().__init__(app)

        self.name = "Skyrim"
        self.id = "Skyrim"
        self.inidir = self.app.doc_path / "My Games" / self.name
        self.inifiles = [
            self.inidir / "Skyrim.ini",
            self.inidir / "SkyrimPrefs.ini",
            self.inidir / "SkyrimCustom.ini",
        ]
        self.reg_paths = [
            "HKEY_LOCAL_MACHINE\\SOFTWARE\\WOW6432Node\\Bethesda Softworks\\Skyrim\\installed path"
        ]

    def __repr__(self):
        return "SkyrimInstance"
