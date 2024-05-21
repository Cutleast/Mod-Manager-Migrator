"""
This file is part of Mod Manager Migrator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

from main import MainApp

from .game import GameInstance


class FalloutNVInstance(GameInstance):
    """
    Class for FalloutNV GameInstance.
    Inherited from GameInstance class.
    """

    icon_name = "FalloutNV.ico"

    def __init__(self, app: MainApp):
        super().__init__(app)

        self.name = "Fallout New Vegas"
        self.id = "FalloutNV"
        self.inidir = self.app.doc_path / "My Games" / self.id
        self.inifiles = [
            self.inidir / "Fallout.ini",
            self.inidir / "FalloutPrefs.ini",
        ]
        self.steamid = 22380
        self.gogid = 1312824873

    def __repr__(self):
        return "FalloutNVInstance"
