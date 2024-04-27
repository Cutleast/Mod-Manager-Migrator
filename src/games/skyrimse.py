"""
This file is part of Mod Manager Migrator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

from main import MainApp

from .game import GameInstance


class SkyrimSEInstance(GameInstance):
    """
    Class for SkyrimSE GameInstance.
    Inherited from GameInstance class.
    """

    icon_name = "Skyrimse.ico"

    def __init__(self, app: MainApp):
        super().__init__(app)

        self.name = "Skyrim Special Edition"
        self.id = "SkyrimSE"
        self.inidir = self.app.doc_path / "My Games" / self.name
        self.inifiles = [
            self.inidir / "Skyrim.ini",
            self.inidir / "SkyrimPrefs.ini",
            self.inidir / "SkyrimCustom.ini",
        ]
        self.steamid = 489830
        self.gogid = 1711230643

    def __repr__(self):
        return "SkyrimSEInstance"
